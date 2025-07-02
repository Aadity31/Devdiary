import streamlit as st
import subprocess
import json
import os
import time
from utils.github_api import get_github_repos
from utils.post_builder import get_scheduled_posts

IGNORED_FILE = "data/ignored_repos.json"

def load_ignored():
    if not os.path.exists(IGNORED_FILE):
        return []
    with open(IGNORED_FILE, "r") as f:
        return json.load(f)

def save_ignored(repos):
    with open(IGNORED_FILE, "w") as f:
        json.dump(repos, f, indent=2)

def trigger_scan():
    try:
        subprocess.run(["python", "core/task_engine.py"], check=True)
        st.info("📡 Repo scan triggered.")
    except Exception as e:
        st.error(f"⚠️ Error triggering scan: {e}")

def main():
    st.set_page_config(page_title="DevDiary.AI Admin Panel", layout="wide")
    st.title("🧠 DevDiary.AI - Admin Panel")
    st.markdown("Manage your AI-generated posts and GitHub automation system.")

    with st.sidebar:
        st.header("⚙️ Actions")
        if st.button("🔄 Trigger Repo Scan"):
            trigger_scan()

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
            caption = post.get("post", "No caption")
            description = post.get("description", "No description")
            tags = post.get("tags", [])
            image_path = post.get("image", "")
            what_is_it = post.get("what_is_it", "")

            # 📸 Side-by-side layout
            st.markdown(f"### 📌 {source}  ⏰ {date}")
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

                bcol1, bcol2 = st.columns([1, 1])
                with bcol1:
                    if st.button("♻️ Regenerate", key=f"regen_{idx}"):
                        st.success(f"♻️ Regenerated post {idx+1}")
                with bcol2:
                    if st.button("❌ Delete", key=f"delete_{idx}"):
                        st.warning("🗑 Delete not implemented yet.")

if __name__ == "__main__":
    main()
