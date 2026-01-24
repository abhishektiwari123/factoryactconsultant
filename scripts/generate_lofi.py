#!/usr/bin/env python3
"""
LoFi music video generator
Creates chill background videos with looping animations and royalty-free music
"""
import asyncio
import os
import random
from pathlib import Path
import httpx
from moviepy import (
    ImageClip, AudioFileClip, CompositeVideoClip,
    ColorClip, TextClip, vfx
)
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

# Config
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
FREESOUND_API_KEY = os.getenv("FREESOUND_API_KEY", "")  # Optional: freesound.org

LOFI_THEMES = [
    "cozy coffee shop window rain",
    "anime bedroom night city view",
    "study desk lamp books aesthetic",
    "rainy window city lights night",
    "sunset bedroom cozy aesthetic",
    "japanese street night aesthetic",
    "library study aesthetic warm",
    "rooftop city view night aesthetic"
]

async def get_pexels_video(query: str, output_path: Path) -> str:
    """Fetch video from Pexels"""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={"query": query, "per_page": 10, "orientation": "landscape"}
        )
        videos = r.json().get("videos", [])
        if videos:
            video = random.choice(videos)
            # Get HD quality video file
            for file in video.get("video_files", []):
                if file.get("quality") == "hd":
                    url = file["link"]
                    break
            else:
                url = video["video_files"][0]["link"]

            vid = await client.get(url, timeout=120)
            output_path.write_bytes(vid.content)
            return str(output_path)
    return ""

async def get_pexels_image(query: str, output_path: Path) -> str:
    """Fetch image from Pexels"""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={"query": query, "per_page": 10, "orientation": "landscape"}
        )
        photos = r.json().get("photos", [])
        if photos:
            url = random.choice(photos)["src"]["large2x"]
            img = await client.get(url)
            output_path.write_bytes(img.content)
            return str(output_path)
    return ""

def create_animated_background(image_path: str, duration: float, output_path: str):
    """Create slow-moving Ken Burns effect on image"""
    clip = ImageClip(image_path).set_duration(duration)

    # Slow zoom and pan effect
    def zoom_effect(t):
        zoom = 1 + 0.1 * (t / duration)
        return zoom

    clip = clip.resize(zoom_effect)
    clip = clip.set_position(lambda t: ('center', 'center'))

    return clip

def add_lofi_overlay(clip, duration: float):
    """Add aesthetic overlay effects"""
    # Create vignette overlay
    w, h = 1920, 1080
    vignette = ColorClip(size=(w, h), color=(0, 0, 0))
    vignette = vignette.set_opacity(0.3).set_duration(duration)

    # Create film grain effect (optional)
    def make_grain_frame(t):
        grain = np.random.randint(0, 30, (h, w, 3), dtype=np.uint8)
        return grain

    return CompositeVideoClip([clip, vignette])

def add_lofi_text(clip, title: str, duration: float):
    """Add aesthetic text overlay"""
    txt = TextClip(
        title,
        fontsize=48,
        color='white',
        font='DejaVu-Sans',
        stroke_color='black',
        stroke_width=1
    ).set_position(('center', 50)).set_duration(duration).set_opacity(0.8)

    return CompositeVideoClip([clip, txt])

async def main(
    music_path: str = None,
    theme: str = None,
    duration_hours: float = 1.0,
    output_name: str = "lofi_video"
):
    output_dir = Path("./outputs")
    output_dir.mkdir(exist_ok=True)
    temp_dir = output_dir / "temp_lofi"
    temp_dir.mkdir(exist_ok=True)

    theme = theme or random.choice(LOFI_THEMES)
    duration = duration_hours * 3600  # Convert to seconds

    print(f"🎵 Creating LoFi video: {theme}")
    print(f"⏱️ Duration: {duration_hours} hour(s)")

    # 1. Get background image/video
    print("🖼️ Fetching background...")
    bg_path = temp_dir / "background.jpg"
    await get_pexels_image(theme, bg_path)

    # 2. Create animated background
    print("🎬 Creating animation...")
    bg_clip = create_animated_background(str(bg_path), min(duration, 3600), str(temp_dir / "bg.mp4"))

    # Loop if needed for longer videos
    if duration > 3600:
        loops = int(duration / 3600) + 1
        bg_clip = bg_clip.loop(loops)
        bg_clip = bg_clip.subclip(0, duration)

    # 3. Add overlays
    print("✨ Adding effects...")
    final = add_lofi_overlay(bg_clip, duration)
    final = add_lofi_text(final, f"☕ {theme.title()} | LoFi Beats", duration)

    # 4. Add music if provided
    if music_path and os.path.exists(music_path):
        print("🎵 Adding music...")
        audio = AudioFileClip(music_path)
        if audio.duration < duration:
            loops = int(duration / audio.duration) + 1
            audio = audio.loop(loops)
        audio = audio.subclip(0, duration)
        final = final.set_audio(audio)

    # 5. Export
    print("💾 Exporting video...")
    output_path = str(output_dir / f"{output_name}.mp4")
    final.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="medium"
    )

    print(f"✅ LoFi video saved: {output_path}")
    return output_path

if __name__ == "__main__":
    import sys
    music = sys.argv[1] if len(sys.argv) > 1 else None
    theme = sys.argv[2] if len(sys.argv) > 2 else None
    hours = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
    asyncio.run(main(music, theme, hours))
