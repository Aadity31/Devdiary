import os
import time
import base64
import psutil
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
CHROME_USER_DATA = "C:\\chrome-temp"
DEBUG_PORT = "9222"
FLUX_URL = "https://huggingface.co/black-forest-labs/FLUX.1-dev"

def launch_chrome_debug():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if "chrome.exe" in proc.info['name'] and f"--remote-debugging-port={DEBUG_PORT}" in ' '.join(proc.info['cmdline']):
            print("🟢 Chrome already running in debug mode.")
            return
    print("🚀 Launching Chrome in debug mode...")
    subprocess.Popen([
        CHROME_PATH,
        f"--remote-debugging-port={DEBUG_PORT}",
        f"--user-data-dir={CHROME_USER_DATA}"
    ])
    time.sleep(3)

def generate_image(prompt: str, save_path: str):
    launch_chrome_debug()

    # Connect to existing Chrome session
    options = Options()
    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{DEBUG_PORT}")
    driver = webdriver.Chrome(service=Service(), options=options)
    wait = WebDriverWait(driver, 30)

    try:
        driver.get(FLUX_URL)
        print(f"🌐 Opened: {FLUX_URL}")

        # Enter prompt
        input_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="Your sentence here..."]')))
        input_box.clear()
        input_box.send_keys(prompt)
        print("📝 Prompt entered.")

        compute_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"].btn-widget')))
        compute_btn.click()
        print("🚀 Compute clicked.")

        # Wait for image to appear in button background
        print("⌛ Waiting for image...")
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[aria-label="View output image"]')))
        time.sleep(5)  # Give some buffer time

        # Extract blob image and convert
        print("📥 Fetching blob image...")
        data_url = driver.execute_async_script("""
            const done = arguments[0];
            const btn = document.querySelector('button[aria-label="View output image"]');
            const style = window.getComputedStyle(btn);
            const match = style.backgroundImage.match(/url\\("(.+?)"\\)/);
            if (!match) return done(null);
            const blobUrl = match[1];
            fetch(blobUrl)
                .then(r => r.blob())
                .then(b => {
                    const reader = new FileReader();
                    reader.onloadend = () => done(reader.result);
                    reader.readAsDataURL(b);
                });
        """)

        if not data_url or not data_url.startswith("data:image/"):
            print("❌ Failed to convert blob to image.")
            return

        # Save the image
        image_data = base64.b64decode(data_url.split(",")[1])
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(image_data)

        print(f"✅ Image saved to: {save_path}")

    except Exception as e:
        print(f"❌ Error generating image: {e}")
    finally:
        driver.quit()
