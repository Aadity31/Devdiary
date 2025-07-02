import os
import json
import subprocess
import time
import pyautogui
import pyperclip
import psutil
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

STACK_PATH = "data/post_stack/active_stack.json"

# === Load Stack Data ===
def load_stack():
    if not os.path.exists(STACK_PATH):
        return []
    with open(STACK_PATH, "r") as f:
        return json.load(f)

# === Trigger ChatGPT Automation if Stack is Empty ===
def ensure_stack_has_data():
    stack = load_stack()
    if not stack:
        print("\U0001F4ED Stack is empty. Running chatgpt_automation.py...")
        subprocess.run(["python", "chatgpt_automation.py"])
        stack = load_stack()
    else:
        print("\U0001F4E6 Stack already has data.")
    return stack

# === Open Chrome in Debug Mode ===
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

# === Open ChatGPT ===
def open_chatgpt():
    subprocess.Popen([
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "--remote-debugging-port=9222",
        "--user-data-dir=C:\\chrome-temp",
        "https://chat.openai.com/"
    ])
    print("🔓 ChatGPT opened in debug Chrome...")
    time.sleep(10)

# === Send Prompt ===
def send_prompt(prompt):
    pyperclip.copy(prompt)
    time.sleep(1)
    pyautogui.hotkey("ctrl", "v")
    pyautogui.press("enter")
    print("🛫 Prompt sent to ChatGPT...")
    time.sleep(5)

# === Scrape Response ===
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

        print(f"📋 Scraped {len(full_response)} characters from ChatGPT response.")
        return full_response

    except Exception as e:
        print("❌ Failed to extract response:", e)
        return ""

    finally:
        driver.quit()

# === Parse JSON Response ===
def parse_response(response):
    try:
        match = re.search(r'\{[\s\S]+\}', response)
        if not match:
            raise ValueError("No JSON block found.")

        json_text = match.group()
        json_text = re.sub(r"[\x00-\x1F]+", " ", json_text)
        json_text = re.sub(r'\n\s+', ' ', json_text)
        return json.loads(json_text)
    except Exception as e:
        print("⚠️ Error parsing JSON:", e)
        return None

# === Generate Content for Learning Post ===
def generate_learning_post(item):
    learning_text = item["text"]
    repo = item["from_repo"]
    date = item["date_added"]

    prompt = f"""
You are an AI social media assistant.

I have learned this recently:
\"{learning_text}\"

Create a creative and technical LinkedIn/Instagram style post about this learning.
Generate:
1. A short social media post text.
2. A compelling image description idea to create a visual for this post.
3. A one-line explanation of what this concept is.
4. A list of 4-5 relevant hashtags.
5. A small paragraph-style description (~40-60 words).

Do NOT include markdown, just plain JSON like:
{{
  "post": "...",
  "image": "...",
  "what_is_it": "...",
  "tags": ["#Python", "#Learning"],
  "description": "..."
}}
"""
    print("\n--- Sending Prompt to ChatGPT ---\n")
    launch_chrome_debug()
    open_chatgpt()
    send_prompt(prompt)
    raw = scrape_response_from_tab()
    response = parse_response(raw)

    if response:
        print("\n✅ Post Content Generated:")
        print(json.dumps(response, indent=2))
    else:
        print("❌ Failed to generate content from ChatGPT.")

# === Main Execution ===
if __name__ == "__main__":
    stack = ensure_stack_has_data()

    if not stack:
        print("❌ No data to generate post.")
    else:
        last_item = stack.pop()  # LIFO
        if last_item["type"] == "learning":
            generate_learning_post(last_item)
        else:
            print("⏩ Skipping item. Only processing learning type for now.")
