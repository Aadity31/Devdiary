import os
import json
import subprocess
import time
import psutil
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
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
        print("📭 Stack is empty. Running chatgpt_automation.py...")
        subprocess.run(["python","-m","core.chatgpt_automation"])
        stack = load_stack()
    else:
        print("📦 Stack already has data.")
    return stack

# === Open Chrome in Debug Mode (only once) ===
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

# === Navigate ChatGPT ===
def open_chatgpt(driver):
    driver.get("https://chat.openai.com/")
    print("🔓 Navigated to ChatGPT in debug Chrome...")
    time.sleep(10)

# === Send Prompt via Selenium (ProseMirror) ===
def send_prompt(driver, prompt):
    print("💬 Sending prompt via Selenium...")
    wait = WebDriverWait(driver, 60)

    input_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.ProseMirror')))
    input_box.click()
    time.sleep(1)

    for line in prompt.splitlines():
        input_box.send_keys(line)
        input_box.send_keys(Keys.SHIFT, Keys.ENTER)

    # Submit prompt using ENTER or button
    try:
        submit_btn = driver.find_element(By.ID, "composer-submit-button")
        submit_btn.click()
    except:
        input_box.send_keys(Keys.ENTER)

    print("🛫 Prompt sent to ChatGPT...")
    time.sleep(5)

# === Scrape JSON response from ChatGPT ===
def scrape_response_from_tab(driver):
    try:
        print("🕒 Waiting for ChatGPT response to complete...")

        wait = WebDriverWait(driver, 120)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.markdown')))

        # Wait for typing to finish
        while True:
            try:
                spinner = driver.find_element(By.CSS_SELECTOR, "div.text-token-stream span[data-testid='cursor']")
                if spinner.is_displayed():
                    print("⏳ ChatGPT is still typing...")
                    time.sleep(2)
                    continue
            except:
                break

        print("✅ ChatGPT finished typing. Now collecting full response...")
        print("🔁 Waiting for response to stabilize...")

        previous_text = ""
        stable_counter = 0

        for _ in range(20):
            elements = driver.find_elements(By.CSS_SELECTOR, 'div.markdown.prose p, div.markdown.prose li')
            if not elements:
                time.sleep(1)
                continue

            last = elements[-1].text.strip()
            if last == previous_text:
                stable_counter += 1
            else:
                stable_counter = 0
                previous_text = last

            if stable_counter >= 3:
                break

            time.sleep(1)

        print("✅ Response stabilized. Final text collected.")
        print(f"📋 Scraped {len(previous_text)} characters from latest response.")
        return previous_text

    except Exception as e:
        print("❌ Failed to extract response:", e)
        return ""



# === Parse JSON safely ===
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

# === Build Prompt Based on Item Type ===
def build_prompt(item):
    text = item["text"]
    type_ = item.get("type", "learning")

    if type_ == "learning":
        intro = f'I have learned this tech recently:\n"{text}"'
    elif type_ == "summary":
        intro = f'I have made this project recently:\n"{text}"'
    elif type_ == "teach":
        intro = f'I have explained this topic to others recently:\n"{text}"'
    elif type_ == "tech":
        intro = f'I have explored this technology recently:\n"{text}"'
    else:
        intro = f'I have discovered this recently:\n"{text}"'

    return f"""
You are an AI social media assistant.

{intro}

Create a creative and technical LinkedIn/Instagram style post about it.
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
# === Load scheduling settings from setting.json ===
def load_schedule_settings():
    try:
        with open("setting.json", "r") as f:
            settings = json.load(f)
            gap = int(settings.get("schedule_gap_days", 0))
            time_str = settings.get("schedule_time", "09:00")
            hour, minute = map(int, time_str.split(":"))
            return gap, hour, minute
    except Exception as e:
        print(f"⚠️ Failed to read setting.json. Defaulting to 0 day gap, 09:00 AM. Error: {e}")
        return 0, 9, 0

# === Apply dynamic schedule to each post ===
def apply_scheduling(posts):
    gap_days, hour, minute = load_schedule_settings()
    now = datetime.now()
    for i, post in enumerate(posts):
        scheduled_dt = now + timedelta(days=i * gap_days)
        scheduled_dt = scheduled_dt.replace(hour=hour, minute=minute, second=0, microsecond=0)
        post["date"] = scheduled_dt.strftime("%Y-%m-%d")
        post["time"] = scheduled_dt.strftime("%H:%M")
    return posts

# === Generate Posts for Valid Items ===
def generate_learning_posts(stack):
    responses = []
    launch_chrome_debug()

    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(service=Service(), options=options)

    try:
        open_chatgpt(driver)

        for idx, item in enumerate(stack):
            if item.get("type") not in {"learning", "summary", "teach", "tech"}:
                print(f"⏭️ Skipping item {idx + 1}: Unsupported type '{item.get('type')}'.")
                continue

            print(f"\n📌 Processing item {idx + 1}/{len(stack)}...")

            prompt = build_prompt(item)
            send_prompt(driver, prompt)
            raw = scrape_response_from_tab(driver)
            response = parse_response(raw)

            if response:
                responses.append({
                    "input": item,
                    "output": response
                })
                print(f"✅ Item {idx + 1} processed successfully.\n")
            else:
                print(f"❌ Failed to get response for item {idx + 1}.")

    finally:
        driver.quit()

    return responses

# === Main Execution ===
if __name__ == "__main__": 
    stack = ensure_stack_has_data()

    if not stack:
        print("❌ No data to process.")
    else:
        collected = generate_learning_posts(stack)
        print(f"\n✅ {len(collected)} posts collected successfully.")

        # ✅ Save to post_prompt.json
        prompt_save_path = "data/post_stack/post_prompt.json"
        os.makedirs(os.path.dirname(prompt_save_path), exist_ok=True)
        with open(prompt_save_path, "w", encoding="utf-8") as f:
            json.dump(collected, f, indent=2, ensure_ascii=False)
        print(f"📝 Saved post prompt data to: {prompt_save_path}")

        # ✅ Auto-run image generation and scheduling
        print("\n🔁 Triggering image generation and scheduling script...\n")
        subprocess.run(["python", "-m", "core.generate_images_and_schedule"])

