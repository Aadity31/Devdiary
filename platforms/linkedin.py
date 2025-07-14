import os
import io
import time
import keyboard
from PIL import Image
import win32clipboard
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def copy_image_to_clipboard(image_path):
    try:
        image = Image.open(image_path).convert("RGB")
        output = io.BytesIO()
        image.save(output, "BMP")
        bmp_data = output.getvalue()[14:]
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, bmp_data)
        win32clipboard.CloseClipboard()
        print(f"📋 Image copied to clipboard: {image_path}")
    except Exception as e:
        print(f"[✗] Clipboard copy failed: {e}")


def simulate_ctrl_v():
    print("[→] Simulating Ctrl+V...")
    keyboard.press_and_release('ctrl+v')
    print("[✓] Ctrl+V simulated")


def post_to_linkedin(driver, post_data):
    wait = WebDriverWait(driver, 25)
    editor_xpath = "//div[contains(@role,'textbox') and contains(@class,'ql-editor')]"

    print("[→] Waiting for LinkedIn to load...")
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print("[✓] LinkedIn loaded.")

    print("[→] Clicking 'Start a post'...")
    start_post_btn = wait.until(EC.element_to_be_clickable((
        By.XPATH, "//button[.//strong[text()='Start a post']]"
    )))
    driver.execute_script("arguments[0].click();", start_post_btn)
    print("[✓] Post dialog opened.")
    time.sleep(2)

    editor = wait.until(EC.presence_of_element_located((By.XPATH, editor_xpath)))
    editor.click()
    time.sleep(1)

    # Step 1: Type post content
    full_text = post_data['post'] + "\n\n" + ' '.join(post_data.get('tags', []))
    editor.send_keys(full_text)
    print("[✓] Post text and tags typed.")
    time.sleep(3)  # Extended wait to ensure box is fully ready

    # Step 2: Copy + Paste Image from Clipboard
    if post_data.get("image"):
        print("[→] Copying image to clipboard...")
        copy_image_to_clipboard(post_data["image"])
        time.sleep(1)

        # Refocus before pasting
        editor.click()
        driver.execute_script("arguments[0].focus();", editor)
        time.sleep(1)

        # Paste twice as backup
        simulate_ctrl_v()
        time.sleep(2)
        simulate_ctrl_v()
        print("[✓] Image paste triggered.")
        time.sleep(3)  # Wait for image to finish uploading/rendering

    # Step 3: Click Post
    print("[→] Clicking Post button...")
    post_btn = wait.until(EC.element_to_be_clickable((
        By.XPATH, "//button[.//span[text()='Post']]"
    )))
    driver.execute_script("arguments[0].click();", post_btn)
    print("🚀 Post submitted successfully ✅")


if __name__ == "__main__":
    post_data = {
        "post": "📢 This post was auto-generated using clipboard-based image paste after adding text first!",
        "tags": ["#AI", "#DevDiary", "#LinkedInAutomation"],
        "image": "data/image/A_tech_stack_for_building_secure,_interactive_Discord_bots_using_Python..png"
    }

    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "localhost:9222")
    driver = webdriver.Chrome(service=Service(), options=chrome_options)

    try:
        post_to_linkedin(driver, post_data)
    finally:
        driver.quit()
        print("[✓] Chrome driver closed.")
