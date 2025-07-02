# utils/github_api.py

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_github_repos():
    GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}"
    }

    params = {
        "visibility": "all",
        "affiliation": "owner,collaborator,organization_member",
        "per_page": 100
    }

    try:
        response = requests.get("https://api.github.com/user/repos", headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            return [repo["full_name"] for repo in data]
        else:
            print("GitHub API error:", response.status_code, response.text)
            return []
    except Exception as e:
        print("Error fetching repos:", e)
        return []

def temp_make_public(repo_full_name, make_private=False):
    """
    Temporarily makes a private repo public (or reverts it if make_private=True).
    Returns True if the repo was originally private.
    """
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Get current repo visibility
    url = f"https://api.github.com/repos/{repo_full_name}"
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        print("⚠️ Failed to fetch repo:", res.text)
        return False

    repo_data = res.json()
    current_private = repo_data.get("private", False)

    if make_private:
        if current_private:
            return False  # already private
        # Revert to private
        patch_res = requests.patch(url, headers=headers, json={"private": True})
        if patch_res.status_code == 200:
            print(f"🔒 Reverted repo {repo_full_name} to private.")
        else:
            print("❌ Failed to revert to private:", patch_res.text)
        return False

    if current_private:
        patch_res = requests.patch(url, headers=headers, json={"private": False})
        if patch_res.status_code == 200:
            print(f"🔓 Temporarily made {repo_full_name} public.")
            return True
        else:
            print("❌ Failed to make public:", patch_res.text)
            return False
    else:
        return False  # already public