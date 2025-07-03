import requests
import webbrowser
import os
from urllib.parse import urlencode

# ENV
CLIENT_ID = os.getenv("x_client_id")
CLIENT_SECRET = os.getenv("x_client_secret")
REDIRECT_URI = "http://localhost:8000/callback"
SCOPES = "tweet.read tweet.write users.read offline.access"

# Step 1: Get Authorization Code
params = {
    "response_type": "code",
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPES,
    "state": "state",
    "code_challenge": "challenge",  # for PKCE
    "code_challenge_method": "plain"
}
auth_url = f"https://twitter.com/i/oauth2/authorize?{urlencode(params)}"
print(f"🔗 Open this URL in browser: {auth_url}")
webbrowser.open(auth_url)

# Step 2: After redirect, you'll get ?code= in browser → paste here
auth_code = input("📥 Enter the authorization code from the URL: ")

# Step 3: Exchange code for access_token
token_resp = requests.post("https://api.twitter.com/2/oauth2/token", data={
    "code": auth_code,
    "grant_type": "authorization_code",
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "code_verifier": "challenge"  # same as above
}, auth=(CLIENT_ID, CLIENT_SECRET))

access_token = token_resp.json().get("access_token")
print("🔐 Access Token:", access_token)

# Step 4: Post Tweet using v2
tweet_resp = requests.post(
    "https://api.twitter.com/2/tweets",
    headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
    json={"text": "🚀 DevDiary tweet via X API v2 OAuth2 flow!"}
)

print("✅ Tweet Response:", tweet_resp.status_code, tweet_resp.text)
