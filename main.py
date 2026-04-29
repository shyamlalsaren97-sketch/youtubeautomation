"""
YouTube Automation Pipeline
Bengali Horror/Story Channel
Claude AI + ElevenLabs + YouTube Data API v3
"""

import os
import json
import time
import logging
import requests
import tempfile
from pathlib import Path
from datetime import datetime

import anthropic
import edge_tts
import asyncio
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    AudioFileClip, ImageClip, concatenate_videoclips,
    CompositeVideoClip, TextClip
)
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY  = os.environ["ANTHROPIC_API_KEY"]
ELEVENLABS_API_KEY = os.environ["ELEVENLABS_API_KEY"]
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")  # Bengali-capable voice

YOUTUBE_CLIENT_ID     = os.environ["YOUTUBE_CLIENT_ID"]
YOUTUBE_CLIENT_SECRET = os.environ["YOUTUBE_CLIENT_SECRET"]
YOUTUBE_REFRESH_TOKEN = os.environ["YOUTUBE_REFRESH_TOKEN"]

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

STORY_TOPICS = [
    "একটি পুরনো বাড়িতে রাতে অদ্ভুত শব্দের রহস্য",
    "গ্রামের শেষ প্রান্তে একটি পরিত্যক্ত মন্দিরের গল্প",
    "মধ্যরাতে ফোন আসে একজন মৃত মানুষের নম্বর থেকে",
    "একটি আয়নায় যে ছায়া দেখা যায় সে কি সত্যিই ছায়া?",
    "রেলস্টেশনে শেষ ট্রেনের অপেক্ষায় একা এক যাত্রী",
    "পুকুরের তলায় হারিয়ে যাওয়া গ্রামের রহস্য",
    "ছোট মেয়েটির অদৃশ্য বন্ধুর পরিচয়",
    "জঙ্গলের মাঝে একটি আলোর উৎস — কেউ কি ডাকছে?",
]


# ── Step 1: Script Generation ────────────────────────────────────────────────
def generate_script(topic: str) -> dict:
    """Claude দিয়ে বাংলা হরর স্ক্রিপ্ট তৈরি করো"""
    log.info(f"স্ক্রিপ্ট তৈরি হচ্ছে: {topic}")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    prompt = f"""তুমি একজন বাংলা ইউটিউব চ্যানেলের জন্য হরর গল্পের স্ক্রিপ্ট লেখক।

বিষয়: {topic}

নিচের JSON ফরম্যাটে একটি সম্পূর্ণ স্ক্রিপ্ট তৈরি করো:
{{
  "title": "ভিডিওর আকর্ষণীয় বাংলা শিরোনাম (৬০ অক্ষরের মধ্যে)",
  "description": "ইউটিউব ভিডিওর বিবরণ (৩-৪ লাইন, বাংলায়, SEO-বান্ধব)",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "narration": "পুরো গল্পের নেরেশন (৪-৫ মিনিটের জন্য, নাটকীয় ও রহস্যময় ভাষায়, ৬০০-৮০০ শব্দ)",
  "thumbnail_text": "থাম্বনেইলে লেখার জন্য ছোট বাক্য (১৫ অক্ষরের মধ্যে)"
}}

শুধু JSON দাও, অন্য কিছু নয়।"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = message.content[0].text.strip()
    # JSON ব্লক পরিষ্কার করো
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    data = json.loads(raw)
    log.info(f"স্ক্রিপ্ট তৈরি হয়েছে: {data['title']}")
    return data


# ── Step 2: Voice Generation ─────────────────────────────────────────────────
def generate_voice(narration: str, output_path: Path) -> Path:
    """ElevenLabs দিয়ে বাংলা ভয়েসওভার তৈরি করো"""
    log.info("ভয়েসওভার তৈরি হচ্ছে...")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": narration,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8,
            "style": 0.3,
            "use_speaker_boost": True
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    audio_file = output_path / "narration.mp3"
    with open(audio_file, "wb") as f:
        f.write(response.content)

    log.info(f"ভয়েস ফাইল সংরক্ষিত: {audio_file}")
    return audio_file


# ── Step 3: Thumbnail Generation ─────────────────────────────────────────────
def create_thumbnail(title: str, thumbnail_text: str, output_path: Path) -> Path:
    """Pillow দিয়ে আকর্ষণীয় থাম্বনেইল তৈরি করো"""
    log.info("থাম্বনেইল তৈরি হচ্ছে...")

    W, H = 1280, 720
    img = Image.new("RGB", (W, H), color=(10, 5, 20))
    draw = ImageDraw.Draw(img)

    # গ্রেডিয়েন্ট ব্যাকগ্রাউন্ড (অন্ধকার নীল থেকে কালো)
    for y in range(H):
        ratio = y / H
        r = int(10 + ratio * 5)
        g = int(5 + ratio * 2)
        b = int(30 + ratio * 10)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # কোণে লাল আভা (ভয়ের পরিবেশ)
    for i in range(120, 0, -1):
        alpha_r = max(0, 180 - i)
        draw.ellipse(
            [W - i*3, H - i*2, W + i, H + i],
            outline=(alpha_r, 0, 0)
        )

    # ফন্ট লোড (ফলব্যাক সহ)
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
        font_tiny  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
    except Exception:
        font_large = ImageFont.load_default()
        font_small = font_large
        font_tiny  = font_large

    # থাম্বনেইল টেক্সট (বড় লাল রঙে)
    txt = thumbnail_text
    bbox = draw.textbbox((0, 0), txt, font=font_large)
    tw = bbox[2] - bbox[0]
    # ছায়া
    draw.text(((W - tw) // 2 + 3, H // 2 - 60 + 3), txt, font=font_large, fill=(100, 0, 0))
    # মূল লেখা
    draw.text(((W - tw) // 2, H // 2 - 60), txt, font=font_large, fill=(220, 30, 30))

    # শিরোনাম (সাদা, নিচে)
    words = title.split()
    lines, line = [], []
    for w in words:
        line.append(w)
        test = " ".join(line)
        bbox = draw.textbbox((0, 0), test, font=font_small)
        if bbox[2] - bbox[0] > W - 100:
            lines.append(" ".join(line[:-1]))
            line = [w]
    if line:
        lines.append(" ".join(line))

    y_start = H // 2 + 40
    for ln in lines[:3]:
        bbox = draw.textbbox((0, 0), ln, font=font_small)
        tw = bbox[2] - bbox[0]
        draw.text(((W - tw) // 2 + 2, y_start + 2), ln, font=font_small, fill=(60, 60, 60))
        draw.text(((W - tw) // 2, y_start), ln, font=font_small, fill=(230, 230, 230))
        y_start += 50

    # চ্যানেল ব্র্যান্ডিং
    brand = "রহস্যের গল্প"
    bbox = draw.textbbox((0, 0), brand, font=font_tiny)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, H - 55), brand, font=font_tiny, fill=(150, 150, 150))

    # বর্ডার
    draw.rectangle([0, 0, W - 1, H - 1], outline=(60, 0, 0), width=6)

    thumb_file = output_path / "thumbnail.jpg"
    img.save(thumb_file, "JPEG", quality=95)
    log.info(f"থাম্বনেইল সংরক্ষিত: {thumb_file}")
    return thumb_file


# ── Step 4: Video Assembly ────────────────────────────────────────────────────
def create_video(audio_file: Path, thumbnail_file: Path, output_path: Path) -> Path:
    """MoviePy দিয়ে ভিডিও তৈরি করো"""
    log.info("ভিডিও তৈরি হচ্ছে...")

    audio_clip = AudioFileClip(str(audio_file))
    duration   = audio_clip.duration

    # থাম্বনেইল ছবিকে পুরো ভিডিওর ব্যাকগ্রাউন্ড হিসেবে ব্যবহার করো
    image_clip = (
        ImageClip(str(thumbnail_file))
        .set_duration(duration)
        .resize((1280, 720))
    )

    video = image_clip.set_audio(audio_clip)

    video_file = output_path / "final_video.mp4"
    video.write_videofile(
        str(video_file),
        fps=24,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile=str(output_path / "temp_audio.m4a"),
        remove_temp=True,
        logger=None
    )

    log.info(f"ভিডিও সংরক্ষিত: {video_file}")
    return video_file


# ── Step 5: YouTube Upload ────────────────────────────────────────────────────
def get_youtube_service():
    """YouTube API সার্ভিস তৈরি করো"""
    creds = Credentials(
        token=None,
        refresh_token=YOUTUBE_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=YOUTUBE_CLIENT_ID,
        client_secret=YOUTUBE_CLIENT_SECRET,
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
    )
    return build("youtube", "v3", credentials=creds)


def upload_to_youtube(video_file: Path, thumbnail_file: Path, script: dict) -> str:
    """YouTube-এ ভিডিও আপলোড করো"""
    log.info("YouTube-এ আপলোড হচ্ছে...")

    youtube = get_youtube_service()

    body = {
        "snippet": {
            "title": script["title"],
            "description": script["description"] + "\n\n#ভৌতিক #হররগল্প #বাংলাগল্প",
            "tags": script["tags"] + ["ভৌতিক গল্প", "বাংলা হরর", "রহস্যের গল্প", "Bengali Horror"],
            "categoryId": "22",  # People & Blogs
            "defaultLanguage": "bn",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        }
    }

    media = MediaFileUpload(str(video_file), chunksize=-1, resumable=True, mimetype="video/mp4")

    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            log.info(f"আপলোড: {int(status.progress() * 100)}%")

    video_id = response["id"]
    log.info(f"ভিডিও আপলোড সম্পন্ন! ID: {video_id}")

    # থাম্বনেইল সেট করো
    youtube.thumbnails().set(
        videoId=video_id,
        media_body=MediaFileUpload(str(thumbnail_file))
    ).execute()
    log.info("থাম্বনেইল সেট করা হয়েছে।")

    return video_id


# ── Main Pipeline ─────────────────────────────────────────────────────────────
def run_pipeline():
    """পুরো পাইপলাইন একসাথে চালাও"""
    log.info("=" * 50)
    log.info("পাইপলাইন শুরু হচ্ছে...")

    # আজকের তারিখ দিয়ে ফোল্ডার তৈরি
    today = datetime.now().strftime("%Y-%m-%d_%H-%M")
    run_dir = OUTPUT_DIR / today
    run_dir.mkdir(exist_ok=True)

    # টপিক বেছে নাও (পালাক্রমে)
    state_file = OUTPUT_DIR / "state.json"
    if state_file.exists():
        state = json.loads(state_file.read_text())
        idx = state.get("topic_index", 0)
    else:
        idx = 0

    topic = STORY_TOPICS[idx % len(STORY_TOPICS)]
    state_file.write_text(json.dumps({"topic_index": idx + 1}))

    try:
        # Step 1
        script = generate_script(topic)
        (run_dir / "script.json").write_text(json.dumps(script, ensure_ascii=False, indent=2))

        # Step 2
        audio_file = generate_voice(script["narration"], run_dir)

        # Step 3
        thumb_file = create_thumbnail(script["title"], script["thumbnail_text"], run_dir)

        # Step 4
        video_file = create_video(audio_file, thumb_file, run_dir)

        # Step 5
        video_id = upload_to_youtube(video_file, thumb_file, script)

        log.info(f"সম্পন্ন! ভিডিও লিঙ্ক: https://youtube.com/watch?v={video_id}")
        log.info("=" * 50)

    except Exception as e:
        log.error(f"পাইপলাইনে সমস্যা: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run_pipeline()
