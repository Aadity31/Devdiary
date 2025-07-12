import json
import os
from datetime import datetime, timedelta

SCHEDULE_PATH = "data/post_stack/schedule.json"

def get_scheduled_posts():
    if not os.path.exists(SCHEDULE_PATH):
        return []

    with open(SCHEDULE_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print("⚠️ schedule.json is corrupted or empty.")
            return []

def reschedule_posts(new_gap_days, base_time="10:30"):
    posts = get_scheduled_posts()
    if not posts:
        return

    start_date = datetime.today()

    for i, post in enumerate(posts):
        post_date = start_date + timedelta(days=i * new_gap_days)
        post["date"] = post_date.strftime("%Y-%m-%d")
        post["time"] = base_time

    with open(SCHEDULE_PATH, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)
