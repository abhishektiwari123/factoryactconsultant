#!/usr/bin/env python3
"""
Sleep/Ambient video generator
Creates ultra-long relaxation videos (8+ hours) with ambient sounds
"""
import asyncio
import os
import random
from pathlib import Path
import httpx
from moviepy.editor import (
    ImageClip, AudioFileClip, CompositeVideoClip,
    ColorClip, TextClip, concatenate_videoclips
)
import numpy as np

# Config
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")

SLEEP_THEMES = {
    "rain": {
        "search": "rain window night cozy",
        "title": "🌧️ Gentle Rain Sounds for Deep Sleep",
        "color_tint": (10, 20, 40)
    },
    "fireplace": {
        "search": "fireplace cozy warm night",
        "title": "🔥 Crackling Fireplace for Relaxation",
        "color_tint": (40, 20, 10)
    },
    "ocean": {
        "search": "ocean waves beach night",
        "title": "🌊 Ocean Waves for Sleep",
        "color_tint": (10, 30, 50)
    },
    "forest": {
        "search": "forest night peaceful nature",
        "title": "🌲 Forest Night Sounds",
        "color_tint": (10, 30, 20)
    },
    "snow": {
        "search": "snow falling window cozy",
        "title": "❄️ Peaceful Snowfall",
        "color_tint": (30, 35, 45)
    },
    "stars": {
        "search": "night sky stars galaxy",
        "title": "⭐ Starry Night for Sleep",
        "color_tint": (5, 5, 20)
    },
    "underwater": {
        "search": "underwater ocean blue calm",
        "title": "🐠 Underwater Ambience",
        "color_tint": (0, 20, 40)
    }
}

async def get_multiple_images(query: str, count: int, output_dir: Path) -> list:
    """Fetch multiple images from Pexels for variety"""
    images = []
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={"query": query, "per_page": count, "orientation": "landscape"}
        )
        photos = r.json().get("photos", [])
        for i, photo in enumerate(photos[:count]):
            url = photo["src"]["large2x"]
            img = await client.get(url, timeout=60)
            path = output_dir / f"bg_{i:03d}.jpg"
            path.write_bytes(img.content)
            images.append(str(path))
    return images

def create_sleep_segment(image_path: str, duration: float, color_tint: tuple):
    """Create a calming video segment from an image"""
    clip = ImageClip(image_path).set_duration(duration)
    clip = clip.resize((1920, 1080))

    # Very slow, subtle zoom
    def slow_zoom(t):
        return 1 + 0.02 * np.sin(t * 0.1)  # Gentle breathing effect

    clip = clip.resize(slow_zoom)

    # Add dark color tint for sleep
    tint = ColorClip(size=(1920, 1080), color=color_tint)
    tint = tint.set_opacity(0.4).set_duration(duration)

    return CompositeVideoClip([clip, tint])

def add_sleep_title(clip, title: str, duration: float):
    """Add title with fade in/out"""
    # Title appears for first 30 seconds
    txt = TextClip(
        title,
        fontsize=56,
        color='white',
        font='DejaVu-Sans',
    ).set_position('center').set_duration(30).set_opacity(0.9)

    # Fade in and out
    txt = txt.crossfadein(3).crossfadeout(5)

    # Timer/duration display (optional)
    timer = TextClip(
        "8 HOURS • Sleep Music",
        fontsize=24,
        color='white',
        font='DejaVu-Sans',
    ).set_position(('center', 600)).set_duration(30).set_opacity(0.6)
    timer = timer.crossfadein(3).crossfadeout(5)

    return CompositeVideoClip([clip, txt, timer])

def create_crossfade_video(segments: list, fade_duration: float = 5.0):
    """Combine segments with smooth crossfades"""
    if len(segments) == 1:
        return segments[0]

    # Add crossfades between segments
    for i in range(len(segments) - 1):
        segments[i] = segments[i].crossfadeout(fade_duration)
        segments[i + 1] = segments[i + 1].crossfadein(fade_duration)

    return concatenate_videoclips(segments, method="compose")

async def main(
    theme: str = "rain",
    duration_hours: float = 8.0,
    audio_path: str = None,
    output_name: str = None
):
    output_dir = Path("./outputs")
    output_dir.mkdir(exist_ok=True)
    temp_dir = output_dir / "temp_sleep"
    temp_dir.mkdir(exist_ok=True)

    if theme not in SLEEP_THEMES:
        theme = random.choice(list(SLEEP_THEMES.keys()))

    config = SLEEP_THEMES[theme]
    duration = duration_hours * 3600
    output_name = output_name or f"sleep_{theme}_{int(duration_hours)}h"

    print(f"😴 Creating sleep video: {config['title']}")
    print(f"⏱️ Duration: {duration_hours} hours ({duration} seconds)")

    # 1. Get multiple background images
    print("🖼️ Fetching backgrounds...")
    images = await get_multiple_images(config["search"], 5, temp_dir)

    if not images:
        print("❌ No images found!")
        return

    # 2. Create segments (each image for ~30 min with slow transitions)
    print("🎬 Creating segments...")
    segment_duration = 1800  # 30 minutes per segment
    num_segments = int(duration / segment_duration) + 1

    segments = []
    for i in range(num_segments):
        img = images[i % len(images)]
        seg_dur = min(segment_duration, duration - i * segment_duration)
        if seg_dur <= 0:
            break
        segment = create_sleep_segment(img, seg_dur, config["color_tint"])
        segments.append(segment)
        print(f"  Segment {i+1}/{num_segments} created")

    # 3. Combine with crossfades
    print("🔗 Combining segments...")
    final = create_crossfade_video(segments, fade_duration=10.0)

    # 4. Add title
    final = add_sleep_title(final, config["title"], duration)

    # 5. Add audio if provided
    if audio_path and os.path.exists(audio_path):
        print("🎵 Adding ambient audio...")
        audio = AudioFileClip(audio_path)
        if audio.duration < duration:
            loops = int(duration / audio.duration) + 1
            audio = audio.loop(loops)
        audio = audio.subclip(0, duration)
        # Reduce volume for sleep
        audio = audio.volumex(0.5)
        final = final.set_audio(audio)

    # 6. Export (use fast preset for long videos)
    print("💾 Exporting video (this may take a while for long videos)...")
    output_path = str(output_dir / f"{output_name}.mp4")
    final.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",  # Fast encoding for long videos
        threads=4
    )

    print(f"✅ Sleep video saved: {output_path}")
    return output_path

if __name__ == "__main__":
    import sys
    theme = sys.argv[1] if len(sys.argv) > 1 else "rain"
    hours = float(sys.argv[2]) if len(sys.argv) > 2 else 8.0
    audio = sys.argv[3] if len(sys.argv) > 3 else None
    asyncio.run(main(theme, hours, audio))
