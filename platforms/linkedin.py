import sys
import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# === Action to run on X.com ===
def my_action(driver, post_data):
    wait = WebDriverWait(driver, 20)

    print("[→] Waiting for page to load...")
    try:
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        print("[✓] Page loaded.")
    except Exception as e:
        print(f"[✗] Page didn't load: {e}")
        return

    # Type Tweet content
    try:
        print("[→] Looking for tweet box...")
        tweet_box = wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, "div[aria-label='Tweet text'], div[aria-multiline='true']"
        )))
        tweet_box.click()
        time.sleep(1)

        full_text = post_data['post'] + '\n' + ' '.join(post_data['tags'])
        tweet_box.send_keys(full_text)
        time.sleep(1)
        tweet_box.send_keys(Keys.ESCAPE)  # Dismiss suggestions
        print("[✓] Tweet content typed and popup closed.")
    except Exception as e:
        print(f"[✗] Could not type tweet: {e}")
        return

    # Upload image (if exists)
    if os.path.exists(post_data['image']):
        try:
            print("[→] Uploading image...")
            file_input = driver.find_element(By.XPATH, "//input[@type='file']")
            file_input.send_keys(os.path.abspath(post_data['image']))
            print("[✓] Image uploaded.")
            time.sleep(3)
        except Exception as e:
            print(f"[!] Failed to upload image: {e}")
    else:
        print(f"[!] Image not found: {post_data['image']}")

    # Post Button Click
    try:
        print("[→] Looking for Post button...")
        try:
            post_button = wait.until(EC.element_to_be_clickable((
                By.XPATH, "//div[@data-testid='tweetButtonInline']"
            )))
        except:
            print("[!] Fallback to full XPath.")
            post_button = wait.until(EC.element_to_be_clickable((
                By.XPATH, "/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/div[3]/div/div[2]/div[1]/div/div/div/div[2]/div[2]/div[2]/div/div/div/button"
            )))

        try:
            post_button.click()
            print("🚀 Tweet posted using .click().")
        except Exception:
            driver.execute_script("arguments[0].click();", post_button)
            print("🚀 Tweet posted using JavaScript click.")

    except Exception as e:
        print(f"[✗] Failed to click Post button: {e}")

# === Direct run disabled ===
# All execution should come via main.py or test wrapper
if __name__ == "__main__":
    print("[✋] Please run this via `main.py`, not directly.")
