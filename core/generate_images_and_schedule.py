import os
import json
from image_gen import generate_image  # Make sure this function is correctly imported
from datetime import datetime

# === Paths ===
POST_PROMPT_PATH = "data/post_stack/post_prompt.json"
SCHEDULE_PATH = "data/post_stack/schedule.json"
IMAGE_DIR = "data/image"
os.makedirs(IMAGE_DIR, exist_ok=True)

# === Load Data ===
def load_post_prompt():
    if not os.path.exists(POST_PROMPT_PATH):
        print("❌ No post prompt data found.")
        return []
    with open(POST_PROMPT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# === Sanitize filename ===
def safe_filename(name):
    return "".join(c if c.isalnum() or c in "_-" else "_" for c in name.lower().replace(" ", "_"))

# === Main Processing ===
def process_posts():
    prompt_data = load_post_prompt()
    if not prompt_data:
        print("❌ No post data to process.")
        return

    schedule = []

    for idx, post in enumerate(prompt_data):
        input_data = post.get("input", {})
        output_data = post.get("output", {})

        required_keys = ["image", "what_is_it", "post", "description", "tags"]
        if not all(k in output_data for k in required_keys):
            print(f"⚠️ Skipping incomplete item {idx + 1}")
            continue

        image_prompt = output_data["image"]
        what_is_it = output_data["what_is_it"]
        image_name = safe_filename(what_is_it) + ".png"
        image_path = os.path.join(IMAGE_DIR, image_name)

        # 🖼️ Generate image only if not already exists
        if not os.path.exists(image_path):
            print(f"🖼️ Generating image {idx + 1}/{len(prompt_data)}: {image_name}")
            try:
                generate_image(image_prompt, image_path)
            except Exception as e:
                print(f"❌ Failed to generate image for item {idx + 1}: {e}")
                continue
        else:
            print(f"⚠️ Image already exists: {image_name}")

        # 📝 Create schedule entry
        schedule.append({
            "source": input_data.get("from_repo", "unknown"),
            "date": input_data.get("date_added", datetime.today().strftime("%Y-%m-%d")),
            "input_text": input_data.get("text", ""),
            "post": output_data.get("post", ""),
            "image": image_path.replace("\\", "/"),
            "description": output_data.get("description", ""),
            "tags": output_data.get("tags", []),
            "what_is_it": output_data.get("what_is_it", "")
        })

    # 💾 Save schedule file
    with open(SCHEDULE_PATH, "w", encoding="utf-8") as f:
        json.dump(schedule, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Schedule saved to: {SCHEDULE_PATH} ({len(schedule)} items)")

# === Entry Point ===
if __name__ == "__main__":
    print("🔁 Triggering image generation and scheduling script...\n")
    process_posts()

# ✅ Delete post_prompt.json only if scheduling succeeded
try:
    if os.path.exists("data/post_stack/post_prompt.json"):
        os.remove("data/post_stack/post_prompt.json")
        print("🧹 Deleted post_prompt.json after successful scheduling.")
except Exception as e:
    print(f"⚠️ Failed to delete post_prompt.json: {e}")