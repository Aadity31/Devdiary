import time
import pyautogui
import pyperclip
import json
import re
import webbrowser
import os
import subprocess
import psutil
from datetime import datetime
from utils.github_api import get_github_repos, temp_make_public

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# === File Paths ===
STACK_PATH = "data/post_stack/active_stack.json"
IGNORED_FILE = "data/ignored_repos.json"
DEBUG_FILE = "data/debug/chatgpt_raw_response.txt"
SCANNED_FILE = "data/scanned_repos.json"

# === Prompt Format ===
PROMPT_TEMPLATE = """
You are an AI content generator for developers.

this is my github repo link i need review on it on this topic :
{repo_url}

Carefully review, code structure, and any documentation provided.
Now return ONLY the response in the following txt strict JSON format txt:
{{
  "summary": " summary of what this project does and solves.",
  "technologies": ["List of core technologies used like Python, Flask, React"],
  "learning_topics": [
    "What can a developer learn from this project (all topics)",
    "Each topic should be one line, actionable and technical"
  ]
}}

Strictly return only the JSON — no explanation, no markdown, no intro.
✅ Return plain JSON (not markdown or explanation)
🚫 Do NOT wrap in backticks
🚫 Do NOT respond if the repo isn't accessible
"""

# === Auto Launch Chrome Debug Mode ===
def launch_chrome_debug():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if "chrome.exe" in proc.info['name'] and "--remote-debugging-port=9222" in ' '.join(proc.info['cmdline']):
            print("🟢 Chrome already running in debug mode.")
            return
    print("🚀 Launching Chrome in debug mode...")
    subprocess.Popen([
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "--remote-debugging-port=9222",
        "--user-data-dir=C:\\chrome-temp"
    ])
    time.sleep(5)

# === Close Chrome Debug Session ===
def close_debug_chrome():
    print("🧼 Closing Chrome in debug mode...")
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] == "chrome.exe" and "--remote-debugging-port=9222" in ' '.join(proc.info['cmdline']):
                print(f"🛑 Terminating Chrome (PID: {proc.info['pid']})")
                proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

# === Loaders & Savers ===
def load_stack():
    if not os.path.exists(STACK_PATH):
        return []
    with open(STACK_PATH, "r") as f:
        return json.load(f)

def save_stack(stack):
    with open(STACK_PATH, "w") as f:
        json.dump(stack, f, indent=2)

def load_ignored():
    if not os.path.exists(IGNORED_FILE):
        return []
    with open(IGNORED_FILE, "r") as f:
        return json.load(f)

def save_scanned(repo_name):
    scanned = []
    if os.path.exists(SCANNED_FILE):
        with open(SCANNED_FILE, "r") as f:
            try:
                scanned = json.load(f)
                if not isinstance(scanned, list):  # fix if bad format
                    print("⚠️ scanned_repos.json was not a list, resetting.")
                    scanned = []
            except Exception as e:
                print("⚠️ Error reading scanned_repos.json:", e)
                scanned = []

    if repo_name not in scanned:
        scanned.append(repo_name)
        with open(SCANNED_FILE, "w") as f:
            json.dump(scanned, f, indent=2)

def get_next_repo_prompt():
    repos = get_github_repos()
    ignored = load_ignored()
    scanned = []
    if os.path.exists(SCANNED_FILE):
        with open(SCANNED_FILE, "r") as f:
            try:
                scanned = json.load(f)
                if not isinstance(scanned, list):
                    print("⚠️ scanned_repos.json was not a list, resetting.")
                    scanned = []
            except Exception as e:
                print("⚠️ Error reading scanned_repos.json:", e)
                scanned = []

    for repo in repos:
        if repo not in ignored and repo not in scanned:
            repo_url = f"https://github.com/{repo}"
            final_prompt = PROMPT_TEMPLATE.format(repo_url=repo_url)
            return repo, repo_url, final_prompt
    return None, None, None

# === Step 1: Open ChatGPT & Send Prompt ===
def open_chatgpt():
    subprocess.Popen([
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "--remote-debugging-port=9222",
        "--user-data-dir=C:\\chrome-temp",
        "https://chat.openai.com/"
    ])
    print("🔓 ChatGPT opened in debug Chrome...")
    time.sleep(10)

def send_prompt(prompt):
    pyperclip.copy(prompt)
    time.sleep(1)
    pyautogui.hotkey("ctrl", "v")
    pyautogui.press("enter")
    print("🛫 Prompt sent to ChatGPT...")
    time.sleep(5)

# === Step 2: Scrape Response from Already Open Tab ===
def scrape_response_from_tab():
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    driver = webdriver.Chrome(service=Service(), options=options)
    try:
        print("🕒 Waiting for ChatGPT response...")

        wait = WebDriverWait(driver, 60)
        paragraphs = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, 'div.markdown p, div.markdown pre')
        ))

        # Try collecting until it includes proper JSON block
        full_response = ""
        for _ in range(10):  # Try up to 10 times, 3s apart
            time.sleep(3)
            paragraphs = driver.find_elements(By.CSS_SELECTOR, 'div.markdown p, div.markdown pre')
            texts = [p.text.strip() for p in paragraphs if p.text.strip()]
            full_response = "\n".join(texts)

            if full_response.strip().startswith('{') and full_response.strip().endswith('}'):
                break

        with open(DEBUG_FILE, "w", encoding="utf-8") as f:
            f.write(full_response)

        print(f"📋 Scraped {len(full_response)} characters from ChatGPT response.")
        return full_response

    except Exception as e:
        print("❌ Failed to extract response:", e)
        return ""

    finally:
        driver.quit()

# === Step 3: Parse and Save ===
def parse_response(response):
    try:
        # Extract block starting with { and ending with }
        match = re.search(r'\{[\s\S]+\}', response)
        if not match:
            raise ValueError("No JSON block found.")

        json_text = match.group()

        # Clean control characters
        json_text = re.sub(r"[\x00-\x1F]+", " ", json_text)
        json_text = re.sub(r'\n\s+', ' ', json_text)
        return json.loads(json_text)

    except Exception as e:
        print("⚠️ Error parsing JSON:", e)
        return None

def push_to_stack(repo_name, data):
    stack = load_stack()
    today = datetime.now().strftime("%Y-%m-%d")

    stack.append({
        "type": "summary",
        "text": data.get("summary", ""),
        "from_repo": repo_name,
        "date_added": today
    })

    techs = data.get("technologies", [])
    if techs:
        stack.append({
            "type": "tech",
            "text": ", ".join(techs),
            "from_repo": repo_name,
            "date_added": today
        })

    for topic in data.get("learning_topics", []):
        stack.append({
            "type": "learning",
            "text": topic,
            "from_repo": repo_name,
            "date_added": today
        })

    save_stack(stack)
    print("✅ Stack updated with new content.")

# === Main Flow ===
def analyze_next_repo():
    try:
        launch_chrome_debug()
        repo_name, repo_url, prompt = get_next_repo_prompt()
        if not repo_url:
            print("❌ No available repos to analyze.")
            return

        was_private = temp_make_public(repo_name)  # Temporarily public if private

        open_chatgpt()
        send_prompt(prompt)
        raw_output = scrape_response_from_tab()
        parsed = parse_response(raw_output)

        if parsed:
            push_to_stack(repo_name, parsed)
            save_scanned(repo_name)
        else:
            print("❌ Failed to get valid response from ChatGPT.")

        if was_private:
            temp_make_public(repo_name, make_private=True)  # Revert visibility

    finally:
        close_debug_chrome()

# === Entry Point ===
if __name__ == "__main__":
    analyze_next_repo()
