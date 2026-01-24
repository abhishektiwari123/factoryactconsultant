#!/usr/bin/env python3
"""
Viral Shorts/Reels generator
Creates engaging 30-60 second vertical videos optimized for TikTok, Instagram, YouTube Shorts
"""
import asyncio
import json
import os
import random
from pathlib import Path
import httpx
import edge_tts
from moviepy.editor import (
    ImageClip, AudioFileClip, CompositeVideoClip,
    ColorClip, TextClip, concatenate_videoclips, vfx
)
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Config
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
TTS_VOICE = "en-US-ChristopherNeural"  # Energetic voice for shorts

# Viral content formats
VIRAL_FORMATS = {
    "facts": {
        "prompt": "Generate 5 mind-blowing facts about {topic}. Each fact should be surprising and shareable. Format as JSON: {{\"facts\": [\"fact1\", \"fact2\", ...]}}",
        "hook": "You won't believe #{num}...",
        "cta": "Follow for more!"
    },
    "tips": {
        "prompt": "Generate 5 quick actionable tips about {topic}. Each tip should be practical and valuable. Format as JSON: {{\"tips\": [\"tip1\", \"tip2\", ...]}}",
        "hook": "Tip #{num} changed everything...",
        "cta": "Save this for later!"
    },
    "mistakes": {
        "prompt": "Generate 5 common mistakes people make with {topic}. Each should be relatable. Format as JSON: {{\"mistakes\": [\"mistake1\", \"mistake2\", ...]}}",
        "hook": "Stop making mistake #{num}!",
        "cta": "Share with someone who needs this!"
    },
    "ranking": {
        "prompt": "Generate a ranking of 5 items related to {topic} from worst to best. Format as JSON: {{\"items\": [{{\"name\": \"item\", \"rank\": 1, \"reason\": \"why\"}}]}}",
        "hook": "Ranking {topic}...",
        "cta": "What's your #1?"
    }
}

async def generate_content(topic: str, format_type: str = "facts") -> dict:
    """Generate viral content using Groq"""
    format_config = VIRAL_FORMATS.get(format_type, VIRAL_FORMATS["facts"])
    prompt = format_config["prompt"].format(topic=topic)

    async with httpx.AsyncClient() as client:
        r = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=60
        )
        content = r.json()["choices"][0]["message"]["content"]
        start = content.find("{")
        end = content.rfind("}") + 1
        return json.loads(content[start:end])

async def get_vertical_image(query: str, output_path: Path) -> str:
    """Fetch portrait-oriented image for shorts"""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={"query": query, "per_page": 10, "orientation": "portrait"}
        )
        photos = r.json().get("photos", [])
        if photos:
            url = random.choice(photos)["src"]["large2x"]
            img = await client.get(url)
            output_path.write_bytes(img.content)
            return str(output_path)
    return ""

async def generate_tts_fast(text: str, output_path: Path) -> tuple:
    """Generate fast-paced TTS for shorts"""
    communicate = edge_tts.Communicate(text, TTS_VOICE, rate="+10%")
    await communicate.save(str(output_path))
    return str(output_path)

def create_text_image(text: str, size: tuple = (1080, 400),
                      font_size: int = 60, color: str = "white") -> np.ndarray:
    """Create text overlay image"""
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()

    # Word wrap
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        test_line = ' '.join(current_line)
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] > size[0] - 40:
            current_line.pop()
            lines.append(' '.join(current_line))
            current_line = [word]
    lines.append(' '.join(current_line))

    # Draw text with shadow
    y = (size[1] - len(lines) * (font_size + 10)) // 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (size[0] - bbox[2]) // 2
        # Shadow
        draw.text((x+3, y+3), line, font=font, fill=(0, 0, 0, 200))
        # Main text
        draw.text((x, y), line, font=font, fill=color)
        y += font_size + 10

    return np.array(img)

def create_short_segment(
    background_path: str,
    text: str,
    audio_path: str,
    segment_num: int
) -> CompositeVideoClip:
    """Create a single segment of the short"""
    audio = AudioFileClip(audio_path)
    duration = audio.duration + 0.5  # Slight padding

    # Background (1080x1920 for vertical)
    bg = ImageClip(background_path).set_duration(duration)
    bg = bg.resize((1080, 1920))

    # Zoom effect
    bg = bg.resize(lambda t: 1 + 0.05 * (t / duration))

    # Number indicator
    num_text = create_text_image(f"#{segment_num}", (200, 150), 80, "yellow")
    num_clip = ImageClip(num_text).set_duration(duration)
    num_clip = num_clip.set_position((50, 200))

    # Main text
    text_img = create_text_image(text, (1000, 600), 50)
    text_clip = ImageClip(text_img).set_duration(duration)
    text_clip = text_clip.set_position(('center', 'center'))

    # Pop-in animation for text
    text_clip = text_clip.crossfadein(0.2)

    # Dark overlay for text readability
    overlay = ColorClip(size=(1080, 800), color=(0, 0, 0))
    overlay = overlay.set_opacity(0.5).set_duration(duration)
    overlay = overlay.set_position(('center', 'center'))

    composite = CompositeVideoClip([bg, overlay, num_clip, text_clip])
    composite = composite.set_audio(audio)

    return composite

async def main(
    topic: str,
    format_type: str = "facts",
    num_items: int = 5,
    output_name: str = None
):
    output_dir = Path("./outputs/shorts")
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = output_dir / "temp"
    temp_dir.mkdir(exist_ok=True)

    output_name = output_name or f"short_{topic.replace(' ', '_')[:20]}"

    print(f"🎬 Creating viral short: {topic}")
    print(f"📱 Format: {format_type}")

    # 1. Generate content
    print("📝 Generating content...")
    content = await generate_content(topic, format_type)
    items = content.get("facts") or content.get("tips") or content.get("mistakes") or content.get("items", [])
    items = items[:num_items]

    # 2. Generate assets for each item
    print("🎨 Creating assets...")
    segments = []

    for i, item in enumerate(items):
        # Handle both string items and dict items
        text = item if isinstance(item, str) else item.get("name", str(item))

        # Get background
        search_query = f"{topic} aesthetic"
        img_path = temp_dir / f"bg_{i}.jpg"
        await get_vertical_image(search_query, img_path)

        # Generate voiceover
        audio_path = temp_dir / f"audio_{i}.mp3"
        await generate_tts_fast(text, audio_path)

        # Create segment
        segment = create_short_segment(str(img_path), text, str(audio_path), i + 1)
        segments.append(segment)
        print(f"  Segment {i+1}/{len(items)} complete")

    # 3. Add hook and CTA
    format_config = VIRAL_FORMATS[format_type]

    # Hook at start
    hook_text = format_config["hook"].format(num=1)
    hook_audio = temp_dir / "hook.mp3"
    await generate_tts_fast(hook_text, hook_audio)
    hook_img = temp_dir / "hook_bg.jpg"
    await get_vertical_image(topic, hook_img)
    hook_segment = create_short_segment(str(hook_img), hook_text, str(hook_audio), 0)

    # CTA at end
    cta_text = format_config["cta"]
    cta_audio = temp_dir / "cta.mp3"
    await generate_tts_fast(cta_text, cta_audio)
    cta_segment = create_short_segment(str(hook_img), cta_text, str(cta_audio), len(items) + 1)

    # 4. Combine all segments
    print("🔗 Combining segments...")
    all_segments = [hook_segment] + segments + [cta_segment]
    final = concatenate_videoclips(all_segments, method="compose")

    # 5. Export
    print("💾 Exporting short...")
    output_path = str(output_dir / f"{output_name}.mp4")
    final.write_videofile(
        output_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        preset="fast"
    )

    duration = final.duration
    print(f"✅ Short saved: {output_path}")
    print(f"⏱️ Duration: {duration:.1f} seconds")

    if duration > 60:
        print("⚠️ Warning: Video is longer than 60 seconds. Consider reducing content.")

    return output_path

if __name__ == "__main__":
    import sys
    topic = sys.argv[1] if len(sys.argv) > 1 else "productivity hacks"
    format_type = sys.argv[2] if len(sys.argv) > 2 else "tips"
    asyncio.run(main(topic, format_type))
