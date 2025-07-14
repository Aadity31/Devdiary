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
from platforms.insta import my_action as post_on_insta
from platforms.linkedin import post_to_linkedin  # ✅ NEW

# Paths
STACK_DIR = ROOT / "data/post_stack"
SCHEDULE_PATH = STACK_DIR / "schedule.json"
ACTIVE_PATH = STACK_DIR / "active_stack.json"
SUMMARY_PATH = STACK_DIR / "post_stack.json"
SETTING_PATH = STACK_DIR / "setting.json"
DONE_PATH = STACK_DIR / "done.json"

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
    save_json(today_posts, ACTIVE_PATH)
    return today_posts

def record_platform(post, platform):
    setting = load_json(SETTING_PATH)
    entry = next((e for e in setting if e.get("source") == post.get("source")), None)

    if entry:
        if "platforms" not in entry:
            entry["platforms"] = []
        if platform not in entry["platforms"]:
            entry["platforms"].append(platform)
    else:
        setting.append({
            "source": post.get("source"),
            "date": post.get("date"),
            "platforms": [platform]
        })

    save_json(setting, SETTING_PATH)

def mark_post_done(post):
    done = load_json(DONE_PATH)
    done.append({
        "source": post.get("source"),
        "timestamp": datetime.now().isoformat()
    })
    save_json(done, DONE_PATH)
    print(f"[✓] Marked as done: {post.get('source')}")

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

        # === Uncomment based on platform target ===
        # success = run_platform(post_on_x, post, "x", "https://x.com/home")
        # success = run_platform(post_on_insta, post, "insta", "https://www.instagram.com")
        success = run_platform(post_to_linkedin, post, "link", "https://www.linkedin.com/feed/")  # ✅ FIXED

        if success:
            mark_post_done(post)
        else:
            print(f"[!] Post failed for {post['source']}. Will retry later.\n")

if __name__ == "__main__":
    run_all()
