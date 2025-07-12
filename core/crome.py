import subprocess
import time
import psutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
DEBUG_PORT = 9222
USER_DATA_DIR = "C:\\chrome-temp"

def is_chrome_debug_running():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if "chrome.exe" in proc.info['name'] and f"--remote-debugging-port={DEBUG_PORT}" in ' '.join(proc.info['cmdline']):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

def kill_debug_chrome():
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if "chrome.exe" in proc.info['name'] and f"--remote-debugging-port={DEBUG_PORT}" in ' '.join(proc.info['cmdline']):
                print(f"[!] Killing existing debug Chrome (PID: {proc.pid})")
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

def launch_chrome_debug():
    if is_chrome_debug_running():
        print("🟢 Chrome already running in debug mode.")
        return

    # Optional: Uncomment if you want to always restart fresh
    # kill_debug_chrome()

    print("🚀 Launching Chrome in debug mode...")
    subprocess.Popen([
        CHROME_PATH,
        f"--remote-debugging-port={DEBUG_PORT}",
        f"--user-data-dir={USER_DATA_DIR}"
    ])
    time.sleep(5)  # Allow Chrome to fully start

def get_debug_driver():
    options = Options()
    options.debugger_address = f"127.0.0.1:{DEBUG_PORT}"
    try:
        driver = webdriver.Chrome(service=Service(), options=options)
        print("[✓] Connected to Chrome Debugger.")
        return driver
    except Exception as e:
        print(f"[✗] Failed to connect to Chrome debugger: {e}")
        return None

def open_and_run(url: str, action_callback):
    launch_chrome_debug()
    driver = get_debug_driver()
    if not driver:
        print("[✗] Chrome driver not available. Aborting.")
        return

    try:
        driver.get(url)
        print(f"[✓] Navigated to {url}")
        action_callback(driver)
        print("[✓] Action completed.")
    except Exception as e:
        print(f"[✗] Error during operation: {e}")
    finally:
        try:
            driver.quit()
            print("[✓] Chrome driver closed.")
        except Exception as e:
            print(f"[!] Error during driver quit: {e}")
