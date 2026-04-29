# 🎬 YouTube অটোমেশন পাইপলাইন
**বাংলা হরর/রহস্য চ্যানেল — সম্পূর্ণ অটো**

> স্ক্রিপ্ট → ভয়েস → ভিডিও → আপলোড — সব প্রতিদিন অটোমেটিক

---

## ফাইল কাঠামো

```
youtube_automation/
├── main.py                        # মূল পাইপলাইন
├── get_token.py                   # YouTube টোকেন পাওয়ার স্ক্রিপ্ট
├── requirements.txt               # Python লাইব্রেরি
├── .gitignore
└── .github/
    └── workflows/
        └── upload.yml             # GitHub Actions (অটো শিডিউল)
```

---

## সেটআপ গাইড (একবারই করতে হবে)

### ধাপ ১ — API Key সংগ্রহ করুন

| সার্ভিস | কোথায় পাবেন | খরচ |
|---------|------------|-----|
| **Anthropic (Claude)** | console.anthropic.com | ফ্রি ক্রেডিট আছে |
| **ElevenLabs** | elevenlabs.io | ফ্রি (১০,০০০ char/মাস) |
| **YouTube Data API** | console.cloud.google.com | ফ্রি |

---

### ধাপ ২ — Google Cloud সেটআপ

1. [console.cloud.google.com](https://console.cloud.google.com) খুলুন
2. নতুন Project তৈরি করুন (যেকোনো নাম)
3. **APIs & Services → Enable APIs** → "YouTube Data API v3" চালু করুন
4. **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID**
5. Application type: **Desktop App**
6. `credentials.json` ডাউনলোড করুন

---

### ধাপ ৩ — YouTube Refresh Token নিন

```bash
pip install google-auth-oauthlib
python get_token.py
```

ব্রাউজার খুলবে → আপনার YouTube চ্যানেলের Google অ্যাকাউন্ট দিয়ে লগইন করুন → অনুমতি দিন।

Terminal-এ তিনটি মান দেখাবে:
- `YOUTUBE_CLIENT_ID`
- `YOUTUBE_CLIENT_SECRET`
- `YOUTUBE_REFRESH_TOKEN`

---

### ধাপ ৪ — GitHub Repository তৈরি করুন

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/আপনার-নাম/youtube-bot.git
git push -u origin main
```

---

### ধাপ ৫ — GitHub Secrets সেট করুন

Repository → **Settings → Secrets and variables → Actions → New repository secret**

এই ৬টি secret যোগ করুন:

| Secret নাম | মান |
|-----------|-----|
| `ANTHROPIC_API_KEY` | Claude API key |
| `ELEVENLABS_API_KEY` | ElevenLabs API key |
| `ELEVENLABS_VOICE_ID` | Voice ID (ফ্রি ভয়েস: `pNInz6obpgDQGcFmaJgB`) |
| `YOUTUBE_CLIENT_ID` | Google OAuth Client ID |
| `YOUTUBE_CLIENT_SECRET` | Google OAuth Client Secret |
| `YOUTUBE_REFRESH_TOKEN` | get_token.py থেকে পাওয়া টোকেন |

---

### ধাপ ৬ — প্রথমবার টেস্ট করুন

GitHub → **Actions → YouTube Auto Upload → Run workflow**

সফল হলে প্রতিদিন বাংলাদেশ সময় **সকাল ১০টায়** অটোমেটিক চলবে।

---

## কাস্টমাইজ করুন

### নতুন গল্পের টপিক যোগ করুন
`main.py` ফাইলে `STORY_TOPICS` লিস্টে নতুন লাইন যোগ করুন:

```python
STORY_TOPICS = [
    "আপনার নতুন গল্পের বিষয়",
    ...
]
```

### আপলোডের সময় পরিবর্তন করুন
`.github/workflows/upload.yml` ফাইলে:
```yaml
- cron: '0 4 * * *'   # UTC 04:00 = BD সকাল ১০টা
```

### চ্যানেলের নাম পরিবর্তন করুন
`main.py` এ `brand = "রহস্যের গল্প"` লাইনটি পরিবর্তন করুন।

---

## সমস্যা হলে

| সমস্যা | সমাধান |
|-------|--------|
| API key কাজ করছে না | Secret-এ ঠিকমতো পেস্ট হয়েছে কিনা দেখুন |
| YouTube upload error | Refresh token মেয়াদ শেষ হলে `get_token.py` আবার চালান |
| ElevenLabs limit শেষ | মাসের শুরুতে রিসেট হয়, অথবা EdgeTTS ব্যবহার করুন (ফ্রি) |
| ভিডিও তৈরি হচ্ছে না | FFmpeg ইনস্টল আছে কিনা নিশ্চিত করুন |
