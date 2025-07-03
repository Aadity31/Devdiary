import os
import json
import time
import base64
from datetime import datetime, timedelta
from core.image_gen import generate_image

# === Paths ===
POST_PROMPT_PATH = "data/post_stack/post_prompt.json"
SCHEDULE_PATH = "data/post_stack/schedule.json"
SETTING_PATH = "data/post_stack/setting.json"
IMAGE_DIR = "data/image"

# === Load Settings ===
with open(SETTING_PATH, "r") as f:
    settings = json.load(f)

SCHEDULE_GAP_DAYS = int(settings.get("schedule_gap_days", 0))
SCHEDULE_TIME_STR = settings.get("schedule_time", "10:00")

# === Load post prompt data ===
if not os.path.exists(POST_PROMPT_PATH):
    print("❌ No post_prompt.json found.")
    exit()

with open(POST_PROMPT_PATH, "r") as f:
    posts = json.load(f)

if not posts:
    print("❌ No posts found in post_prompt.json.")
    exit()

# === Load existing schedule ===
if os.path.exists(SCHEDULE_PATH):
    with open(SCHEDULE_PATH, "r") as f:
        schedule = json.load(f)
else:
    schedule = []

# === Start scheduling ===
print("\n📆 Starting scheduling process...")
base_date = datetime.today().date()

for idx, post in enumerate(posts):
    input_data = post.get("input")
    output_data = post.get("output")

    if not input_data or not output_data:
        print(f"⚠️ Skipping incomplete item {idx + 1}")
        continue

    # Prepare image
    image_prompt = output_data.get("image")
    image_name = output_data.get("what_is_it", f"post_{idx+1}").replace(" ", "_") + ".png"
    image_path = os.path.join(IMAGE_DIR, image_name)

    try:
        generate_image(image_prompt, image_path)
    except Exception as e:
        print(f"❌ Error generating image for item {idx+1}: {e}")
        continue

    # Calculate scheduled datetime
    scheduled_date = base_date + timedelta(days=idx * SCHEDULE_GAP_DAYS)
    scheduled_time = datetime.strptime(SCHEDULE_TIME_STR, "%H:%M").time()
    scheduled_datetime = datetime.combine(scheduled_date, scheduled_time)

    schedule.append({
        "source": input_data.get("from_repo", "unknown"),
        "date": scheduled_datetime.strftime("%Y-%m-%d"),
        "time": scheduled_datetime.strftime("%H:%M"),
        "input_text": input_data.get("text", ""),
        "post": output_data.get("post", ""),
        "image": image_path.replace("\\", "/"),
        "description": output_data.get("description", ""),
        "tags": output_data.get("tags", []),
        "what_is_it": output_data.get("what_is_it", "")
    })

    print(f"✅ Scheduled post {idx+1} for {scheduled_datetime.strftime('%Y-%m-%d %H:%M')}")

# === Save final schedule ===
with open(SCHEDULE_PATH, "w") as f:
    json.dump(schedule, f, indent=2)

print(f"\n✅ Schedule saved to: {SCHEDULE_PATH} ({len(schedule)} total items)")

# === Clear post_prompt.json ===
os.remove(POST_PROMPT_PATH)
print("🧹 Cleared post_prompt.json after successful scheduling.")
