import os
import json
import time
import base64
from datetime import datetime, timedelta
from core.image_gen import generate_image

# === Paths ===
POST_PROMPT_PATH = "data/post_stack/post_prompt.json"
SCHEDULE_PATH = "data/post_stack/schedule.json"
SETTING_PATH = "data/setting.json"
IMAGE_DIR = "data/image"

# === Emoji remover (optional)
import re
def remove_emojis(text):
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002700-\U000027BF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA70-\U0001FAFF"
        "\U00002600-\U000026FF"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

# === Load Settings ===
with open(SETTING_PATH, "r", encoding="utf-8") as f:
    settings = json.load(f)

SCHEDULE_GAP_DAYS = int(settings.get("schedule_gap_days", 0))
SCHEDULE_TIME_STR = settings.get("schedule_time", "10:00")

# === Load post prompt data ===
if not os.path.exists(POST_PROMPT_PATH):
    print("❌ No post_prompt.json found.")
    exit()

with open(POST_PROMPT_PATH, "r", encoding="utf-8") as f:
    posts = json.load(f)

if not posts:
    print("❌ No posts found in post_prompt.json.")
    exit()

# === Load existing schedule ===
if os.path.exists(SCHEDULE_PATH):
    with open(SCHEDULE_PATH, "r", encoding="utf-8") as f:
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
    image_prompt = remove_emojis(output_data.get("image", ""))
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

    schedule.insert(0,{
        "source": input_data.get("from_repo", "unknown"),
        "date": scheduled_datetime.strftime("%Y-%m-%d"),
        "time": scheduled_datetime.strftime("%H:%M"),
        "input_text": remove_emojis(input_data.get("text", "")),
        "type":remove_emojis(input_data.get("type","")),
        "post": remove_emojis(output_data.get("post", "")),
        "image": image_path.replace("\\", "/"),
        "description": remove_emojis(output_data.get("description", "")),
        "tags": [remove_emojis(tag) for tag in output_data.get("tags", [])],
        "what_is_it": remove_emojis(output_data.get("what_is_it", ""))
    })

    print(f"✅ Scheduled post {idx+1} for {scheduled_datetime.strftime('%Y-%m-%d %H:%M')}")

# === Save final schedule ===
with open(SCHEDULE_PATH, "w", encoding="utf-8") as f:
    json.dump(schedule, f, indent=2, ensure_ascii=False)

print(f"\n✅ Schedule saved to: {SCHEDULE_PATH} ({len(schedule)} total items)")

# === Clear post_prompt.json ===
os.remove(POST_PROMPT_PATH)
print("🧹 Cleared post_prompt.json after successful scheduling.")
