import streamlit as st
import subprocess
import json
import os
import time
from datetime import datetime
from utils.github_api import get_github_repos
from utils.post_builder import get_scheduled_posts, reschedule_posts

IGNORED_FILE = "data/ignored_repos.json"
SETTINGS_FILE = "data/setting.json"
SCHEDULE_FILE = "data/post_stack/schedule.json"

def load_ignored():
    if not os.path.exists(IGNORED_FILE):
        return []
    with open(IGNORED_FILE, "r") as f:
        return json.load(f)

def save_ignored(repos):
    with open(IGNORED_FILE, "w") as f:
        json.dump(repos, f, indent=2)

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {"schedule_gap_days": 1, "schedule_time": "10:30"}
    with open(SETTINGS_FILE, "r") as f:
        return json.load(f)

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

def delete_post(index):
    if not os.path.exists(SCHEDULE_FILE):
        return

    with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
        schedule = json.load(f)

    if index < len(schedule):
        # ✅ Delete image file if exists
        image_path = schedule[index].get("image", "")
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
            print(f"🗑 Deleted image: {image_path}")

        # ✅ Remove the post
        schedule.pop(index)

        with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
            json.dump(schedule, f, indent=2, ensure_ascii=False)

        st.success(f"🗑 Post {index + 1} and its image deleted successfully.")


def main():
    st.set_page_config(page_title="DevDiary.AI Admin Panel", layout="wide")
    st.title("🧠 DevDiary.AI - Admin Panel")
    st.markdown("Manage your AI-generated posts and GitHub automation system.")

    with st.sidebar:
        st.subheader("🕒 Schedule Settings")
        settings = load_settings()
        col1, col2 = st.columns(2)
        with col1:
            gap_days = st.number_input("📆 Gap Between Posts (days)", min_value=0, max_value=30, value=settings.get("schedule_gap_days", 1), format="%d")
        with col2:
            schedule_time = st.time_input("⏰ Schedule Time", value=datetime.strptime(settings.get("schedule_time", "10:30"), "%H:%M").time())

        if st.button("💾 Save Settings"):
            old_gap = settings.get("schedule_gap_days", 1)
            settings["schedule_gap_days"] = gap_days
            settings["schedule_time"] = schedule_time.strftime("%H:%M")
            save_settings(settings)
            st.success("✅ Settings saved.")
            if gap_days != old_gap:
                reschedule_posts(gap_days, settings["schedule_time"])
                st.success("📆 All posts rescheduled with new gap.")



        st.markdown("---")
        st.subheader("📂 GitHub Projects")

        repos = get_github_repos()
        ignored = load_ignored()

        if repos:
            for repo in repos:
                if repo in ignored:
                    st.markdown(f"- ❌ `{repo}` _(Ignored)_")
                else:
                    col1, col2 = st.columns([0.8, 0.2])
                    with col1:
                        st.markdown(f"- `{repo}`")
                    with col2:
                        if st.button("Ignore", key=f"ignore_{repo}"):
                            ignored.append(repo)
                            save_ignored(ignored)
                            time.sleep(0.2)
                            st.rerun()
        else:
            st.warning("⚠️ No repos found or invalid credentials.")

    st.markdown("---")
    with st.expander("📋 Ignored Repositories"):
        if ignored:
            for repo in ignored:
                col1, col2 = st.columns([0.8, 0.2])
                with col1:
                    st.markdown(f"- `{repo}`")
                with col2:
                    if st.button("Unignore", key=f"unignore_{repo}"):
                        ignored.remove(repo)
                        save_ignored(ignored)
                        time.sleep(0.2)
                        st.rerun()
        else:
            st.info("No repos are currently ignored.")

    st.markdown("---")
    st.subheader("📋 Scheduled Posts")
    posts = get_scheduled_posts()
    if not posts:
        st.info("No scheduled posts found.")
    else:
        for idx, post in enumerate(posts):
            source = post.get("source", "Unknown")
            date = post.get("date", "N/A")
            time_val = post.get("time","N/A")
            caption = post.get("post", "No caption")
            description = post.get("description", "No description")
            tags = post.get("tags", [])
            image_path = post.get("image", "")
            what_is_it = post.get("what_is_it", "")

            st.markdown(f"### 📌 {source}  ⏰ {date} 🕒 {time_val}")
            col1, col2 = st.columns([1, 2])

            with col1:
                if image_path and os.path.exists(image_path):
                    st.image(image_path, width=300)
                else:
                    st.warning("⚠️ Image not found or path invalid.")

            with col2:
                st.markdown(f"**🧾 What is it:** {what_is_it}")
                st.markdown(f"**📢 Post Caption:** {caption}")
                st.markdown(f"**📝 Description:** {description}")
                st.markdown(f"**🏷 Tags:** {' '.join(tags)}")

                if st.button("❌ Delete", key=f"delete_{idx}"):
                    delete_post(idx)
                    time.sleep(0.5)
                    st.rerun()

if __name__ == "__main__":
    main()
