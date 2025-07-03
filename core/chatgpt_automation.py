import os
import time
import json
import re
import subprocess
import psutil
from datetime import datetime
from utils.github_api import get_github_repos, temp_make_public

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# === Paths ===
STACK_PATH = "data/post_stack/active_stack.json"
IGNORED_FILE = "data/ignored_repos.json"
DEBUG_FILE = "data/debug/chatgpt_raw_response.txt"
SCANNED_FILE = "data/scanned_repos.json"

# === Prompt Template ===
PROMPT_TEMPLATE = """
You are an AI content generator for developers.
this is my github repo link i need review on it on this topic :
{repo_url}

Carefully review, code structure, and any documentation provided.
Now return ONLY the response in the following strict JSON format:
{{
  "summary": " summary of what this project does and solves.",
  "technologies": ["List of core technologies used like Python, Flask, React"],
  "learning_topics": [
    "What can a developer learn from this project (all topics)",
    "Each topic should be one line, actionable and technical"
  ]
}}

Strictly return only the JSON — no explanation, no markdown, no intro.
 Return plain JSON (not markdown or explanation)
 Do NOT wrap in backticks
 Do NOT respond if the repo isn't accessible
"""

# === Utility: Remove emojis and unsupported characters ===
def remove_non_bmp(text):
    return ''.join(c for c in text if ord(c) <= 0xFFFF)

# === Chrome Launch ===
def launch_chrome_debug():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == "chrome.exe" and "--remote-debugging-port=9222" in ' '.join(proc.info['cmdline']):
                print("🟢 Chrome already running in debug mode.")
                return
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    print("🚀 Launching Chrome in debug mode...")
    subprocess.Popen([
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "--remote-debugging-port=9222",
        "--user-data-dir=C:\\chrome-temp",
        "--no-first-run", "--no-default-browser-check"
    ])
    time.sleep(5)  # give it time to boot and bind port


def close_debug_chrome():
    print("🧼 Closing Chrome in debug mode...")
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == "chrome.exe" and "--remote-debugging-port=9222" in ' '.join(proc.info['cmdline']):
                print(f"🚩 Terminating Chrome (PID: {proc.info['pid']})")
                proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

# === ChatGPT Automation ===
def generate_response_from_prompt(prompt):
    responses = []
    launch_chrome_debug()

    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    # Retry connecting to Chrome
    for attempt in range(5):
        try:
            driver = webdriver.Chrome(service=Service(), options=options)
            break
        except Exception as e:
            print(f"⏳ Waiting for Chrome to be ready... attempt {attempt+1}/5")
            time.sleep(3)
    else:
        print("❌ Failed to connect to Chrome debug session.")
        return None

    try:
        driver.get("https://chat.openai.com/")
        print("🔓 Opening ChatGPT...")
        time.sleep(10)

        wait = WebDriverWait(driver, 60)
        input_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.ProseMirror')))
        input_box.click()
        time.sleep(1)

        for line in prompt.splitlines():
            input_box.send_keys(remove_non_bmp(line))
            input_box.send_keys(Keys.SHIFT, Keys.ENTER)

        try:
            driver.find_element(By.ID, "composer-submit-button").click()
        except:
            input_box.send_keys(Keys.ENTER)

        print("🛫 Prompt sent. Waiting for response...")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.markdown')))
        time.sleep(30)

        # Wait until response is stable
        stable_counter = 0
        previous = ""
        for _ in range(30):
            try:
                spinner = driver.find_element(By.CSS_SELECTOR, "div.text-token-stream span[data-testid='cursor']")
                if spinner.is_displayed():
                    print("⏳ Still typing...")
                    time.sleep(2)
                    continue
            except:
                pass

            elements = driver.find_elements(By.CSS_SELECTOR, 'div.markdown.prose p, div.markdown.prose li')
            current = "\n".join([e.text for e in elements])
            if current.strip() == previous.strip():
                stable_counter += 1
            else:
                stable_counter = 0
                previous = current

            if stable_counter >= 3:
                break
            time.sleep(2)

        print("✅ Finished typing. Collecting response...")
        elements = driver.find_elements(By.CSS_SELECTOR, 'div.markdown.prose p, div.markdown.prose li')
        full_text = "\n".join([e.text for e in elements])

        with open(DEBUG_FILE, "w", encoding="utf-8") as f:
            f.write(full_text)

        return full_text

    except Exception as e:
        print("❌ Error during prompt automation:", e)
        return None


    # ❌ DON'T quit chrome here to keep debug session alive
    # finally:
    #     driver.quit()

# === Stack Utilities ===
def load_stack():
    if not os.path.exists(STACK_PATH): return []
    with open(STACK_PATH, "r") as f: return json.load(f)

def save_stack(stack):
    with open(STACK_PATH, "w") as f: json.dump(stack, f, indent=2)

def load_ignored():
    if not os.path.exists(IGNORED_FILE): return []
    with open(IGNORED_FILE, "r") as f: return json.load(f)

def save_scanned(repo_name):
    scanned = []
    if os.path.exists(SCANNED_FILE):
        with open(SCANNED_FILE, "r") as f:
            try:
                scanned = json.load(f)
                if not isinstance(scanned, list): scanned = []
            except: scanned = []
    if repo_name not in scanned:
        scanned.append(repo_name)
        with open(SCANNED_FILE, "w") as f: json.dump(scanned, f, indent=2)

# === Repo & Prompt Handler ===
def get_next_repo_prompt():
    repos = get_github_repos()
    ignored = load_ignored()
    scanned = []
    if os.path.exists(SCANNED_FILE):
        with open(SCANNED_FILE, "r") as f:
            try:
                scanned = json.load(f)
                if not isinstance(scanned, list): scanned = []
            except: scanned = []

    for repo in repos:
        if repo not in ignored and repo not in scanned:
            repo_url = f"https://github.com/{repo}"
            final_prompt = PROMPT_TEMPLATE.format(repo_url=repo_url)
            return repo, repo_url, final_prompt
    return None, None, None

# === JSON Parser ===
def parse_response(response):
    try:
        match = re.search(r'\{[\s\S]+\}', response)
        if not match:
            raise ValueError("No JSON block found.")
        json_text = match.group()
        json_text = json_text.replace("“", '"').replace("”", '"').replace("’", "'")
        json_text = re.sub(r"[\x00-\x1F]+", " ", json_text)
        json_text = re.sub(r'\n\s+', ' ', json_text)
        return json.loads(json_text)
    except Exception as e:
        print("⚠️ Error parsing JSON:", e)
        return None

# === Save to Stack ===
def push_to_stack(repo_name, data):
    stack = load_stack()
    today = datetime.now().strftime("%Y-%m-%d")
    stack.append({"type": "summary", "text": data.get("summary", ""), "from_repo": repo_name, "date_added": today})
    techs = data.get("technologies", [])
    if techs:
        stack.append({"type": "tech", "text": ", ".join(techs), "from_repo": repo_name, "date_added": today})
    for topic in data.get("learning_topics", []):
        stack.append({"type": "learning", "text": topic, "from_repo": repo_name, "date_added": today})
    save_stack(stack)
    print("✅ Stack updated with new content.")

# === Main Entry ===
def analyze_next_repo():
    try:
        launch_chrome_debug()
        repo_name, repo_url, prompt = get_next_repo_prompt()
        if not repo_url:
            print("❌ No available repos to analyze.")
            return
        was_private = temp_make_public(repo_name)
        response = generate_response_from_prompt(prompt)
        parsed = parse_response(response)
        if parsed:
            push_to_stack(repo_name, parsed)
            save_scanned(repo_name)
        else:
            print("❌ Failed to get valid response.")
        if was_private:
            temp_make_public(repo_name, make_private=True)
    finally:
        print("lululu")
        # close_debug_chrome()

# === Run Script ===
if __name__ == "__main__":
    analyze_next_repo()
