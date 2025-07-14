import os
import json
from datetime import datetime
from pathlib import Path
import sys

# Ensure root path is added
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

# Import platform handlers
from core.crome import open_and_run
from platforms.x import my_action as post_on_x
from platforms.linkedin import post_to_linkedin  # ✅ NEW

# Paths
STACK_DIR = ROOT / "data/post_stack"
SCHEDULE_PATH = STACK_DIR / "schedule.json"
ACTIVE_PATH = STACK_DIR / "active_stack.json"
SETTING_PATH = STACK_DIR / "setting.json"

def load_json(path):
    if not path.exists():
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def get_today_posts():
    today = datetime.now().strftime("%Y-%m-%d")
    schedule = load_json(SCHEDULE_PATH)
    today_posts = [p for p in schedule if p.get("date") == today]
    save_json(today_posts, ACTIVE_PATH)  # Save active stack
    return today_posts

def record_platform(post, platform):
    setting = load_json(SETTING_PATH)
    entry = next((e for e in setting if e.get("source") == post.get("source")), None)

    if entry:
        entry.setdefault("platforms", [])
        if platform not in entry["platforms"]:
            entry["platforms"].append(platform)
    else:
        setting.append({
            "source": post.get("source"),
            "date": post.get("date"),
            "platforms": [platform]
        })

    save_json(setting, SETTING_PATH)

def run_platform(driver_func, post, platform_name, url):
    try:
        open_and_run(url, lambda d: driver_func(d, post))
        print(f"[✓] Posted on {platform_name}")
        record_platform(post, platform_name)
        return True
    except Exception as e:
        print(f"[✗] Failed to post on {platform_name}: {e}")
        return False

def run_all():
    today_posts = get_today_posts()
    for post in today_posts:
        print(f"\n[→] Running post for source: {post['source']}")

        # === Add/Remove Platforms as Needed ===
        posted_anywhere = False
        posted_anywhere |= run_platform(post_on_x, post, "x", "https://x.com/home")
        posted_anywhere |= run_platform(post_to_linkedin, post, "link", "https://www.linkedin.com/feed/")

        if not posted_anywhere:
            print(f"[!] Post failed for {post['source']}. Will retry later.\n")

if __name__ == "__main__":
    run_all()
