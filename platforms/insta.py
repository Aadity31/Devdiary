# run insta.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.crome import open_and_run
from selenium.webdriver.common.by import By
import time

def my_action(driver):
    print("[→] Waiting for page to load...")
    time.sleep(3)


    # Example: Try clicking on the 'Post' button if visible
    try:
        post_button = driver.find_element(By.XPATH, "//span[text()='Post']")
        post_button.click()
        print("[✓] Post button clicked")
    except:
        print("[!] Post button not found (may require login)")

# Run this file directly
if __name__ == "__main__":
    open_and_run("https://www.instagram.com/", my_action)
