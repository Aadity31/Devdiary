import os
import time
import json
import re
import subprocess
import psutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# === Launch Chrome in Debug Mode ===
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

# === Open ChatGPT Website ===
def open_chatgpt(driver):
    driver.get("https://chat.openai.com/")
    print("🔓 Navigated to ChatGPT...")
    time.sleep(10)

# === Send Prompt to ChatGPT ===
def send_prompt(driver, prompt):
    wait = WebDriverWait(driver, 60)
    input_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.ProseMirror')))
    input_box.click()
    time.sleep(1)

    for line in prompt.splitlines():
        input_box.send_keys(line)
        input_box.send_keys(Keys.SHIFT, Keys.ENTER)

    try:
        submit_btn = driver.find_element(By.ID, "composer-submit-button")
        submit_btn.click()
    except:
        input_box.send_keys(Keys.ENTER)

    print("🛫 Prompt sent. Waiting for response...")
    time.sleep(5)

# === Scrape Response ===
def scrape_response_from_tab(driver):
    wait = WebDriverWait(driver, 120)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.markdown')))

    while True:
        try:
            spinner = driver.find_element(By.CSS_SELECTOR, "div.text-token-stream span[data-testid='cursor']")
            if spinner.is_displayed():
                print("⏳ Still typing...")
                time.sleep(2)
                continue
        except:
            break

    print("✅ Finished typing. Collecting response...")

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

    full_text = "\n".join([e.text for e in elements])
    print("📋 Response collected.")
    return full_text

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

# === Main Function ===
def generate_post_from_prompt(prompt):
    launch_chrome_debug()
    options = Options()
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(service=Service(), options=options)

    try:
        open_chatgpt(driver)
        send_prompt(driver, prompt)
        raw = scrape_response_from_tab(driver)
        return parse_response(raw)
    finally:
        driver.quit()

# === Example Usage ===
if __name__ == "__main__":
    sample_prompt = """
You are an AI social media assistant.

I have explored the HuggingFace Transformers library recently.

Create a creative and technical LinkedIn/Instagram style post about it.
Generate:
1. A short social media post text.
2. A compelling image description idea to create a visual for this post.
3. A one-line explanation of what this concept is.
4. A list of 4-5 relevant hashtags.
5. A small paragraph-style description (~40-60 words).

Do NOT include markdown, just plain JSON like:
{
  "post": "...",
  "image": "...",
  "what_is_it": "...",
  "tags": ["#Python", "#Learning"],
  "description": "..."
}
"""

    result = generate_post_from_prompt(sample_prompt)
    print("\n🎯 Final Output:\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))
