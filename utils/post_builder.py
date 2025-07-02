import json
import os

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
