"""
এই স্ক্রিপ্টটি একবার নিজের PC-তে চালান।
YouTube Refresh Token পাবেন, সেটা GitHub Secrets-এ রাখুন।

চালানোর নিয়ম:
  pip install google-auth-oauthlib
  python get_token.py
"""

import json
from google_auth_oauthlib.flow import InstalledAppFlow

# আপনার Google Cloud Console থেকে ডাউনলোড করা credentials.json ফাইল
CLIENT_SECRETS_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def main():
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    creds = flow.run_local_server(port=8080)

    print("\n✅ সফলভাবে টোকেন পাওয়া গেছে!\n")
    print("নিচের তথ্যগুলো GitHub Secrets-এ রাখুন:\n")
    print(f"YOUTUBE_CLIENT_ID     = {creds.client_id}")
    print(f"YOUTUBE_CLIENT_SECRET = {creds.client_secret}")
    print(f"YOUTUBE_REFRESH_TOKEN = {creds.refresh_token}")

    # ফাইলেও সেভ করো
    token_data = {
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "refresh_token": creds.refresh_token,
    }
    with open("youtube_tokens.json", "w") as f:
        json.dump(token_data, f, indent=2)
    print("\n📁 youtube_tokens.json ফাইলেও সেভ হয়েছে।")
    print("⚠️  এই ফাইলটি কখনো GitHub-এ পুশ করবেন না!")

if __name__ == "__main__":
    main()
