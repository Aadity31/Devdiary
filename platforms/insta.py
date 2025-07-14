import sys
import os
import time
import pyautogui
import random

# === Ensure core path is accessible ===
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.crome import open_and_run  # must open instagram.com in debug session

def move_and_click(x, y, label="element"):
    rx, ry = random.randint(-3, 3), random.randint(-3, 3)
    duration = random.uniform(0.2, 0.5)
    pyautogui.moveTo(x + rx, y + ry, duration=duration)
    pyautogui.click()
    print(f"[✓] Clicked on {label}")

def post_on_instagram_gui(post_data):
    print("🚀 Starting Instagram Auto Post...")

    time.sleep(5)  # Wait for Chrome to load
    print("[→] Focusing Instagram tab...")
    pyautogui.click()  # Focus window if not already

    # === Step 1: Click '+' (Create)
    move_and_click(1800, 220, "'+' (Create)")
    time.sleep(random.uniform(1.0, 1.8))

    # === Step 2: Click 'Post' from submenu
    move_and_click(1720, 370, "'Post' submenu")
    time.sleep(random.uniform(2.0, 2.5))

    # === Step 3: Upload image in file dialog
    try:
        image_path = os.path.abspath(post_data['image'])
        pyautogui.write(image_path, interval=0.05)
        pyautogui.press('enter')
        print(f"[✓] Uploaded image: {image_path}")
        time.sleep(random.uniform(4.5, 6.0))
    except Exception as e:
        print(f"[✗] Image upload failed: {e}")
        return

    # === Step 4: Click First 'Next' Button (Edit Filter)
    move_and_click(1600, 900, "First 'Next'")
    time.sleep(random.uniform(2.0, 2.5))

    # === Step 5: Click Second 'Next' Button (Caption screen)
    move_and_click(1600, 900, "Second 'Next'")
    time.sleep(random.uniform(1.5, 2.2))

    # === Step 6: Type caption + tags
    try:
        full_text = post_data['post'] + '\n' + ' '.join(post_data['tags'])
        pyautogui.write(full_text, interval=0.03)
        print("[✓] Caption and tags added.")
        time.sleep(random.uniform(1.0, 1.5))
    except Exception as e:
        print(f"[✗] Could not write caption: {e}")
        return

    # === Step 7: Click Share Button
    move_and_click(1600, 900, "'Share'")
    print("🚀 Post shared successfully!")
    time.sleep(3)

# === Function used by main.py ===
def my_action(driver, post_data):
    post_on_instagram_gui(post_data)

# === Prevent direct execution ===
if __name__ == "__main__":
    print("[✋] Please run this via `main.py` or automation wrapper.")
