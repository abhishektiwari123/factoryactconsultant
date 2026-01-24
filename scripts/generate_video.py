#!/usr/bin/env python3
"""
Quick video generator using MoneyPrinterTurbo API or direct generation
"""
import asyncio
import json
import os
import random
from pathlib import Path
import httpx
import edge_tts
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

# Config
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")  # FREE: console.groq.com
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")  # FREE: pexels.com/api
TTS_VOICE = "en-US-AndrewNeural"

async def generate_script(topic: str, scenes: int = 10) -> list:
    """Generate video script using Groq (FREE)"""
    prompt = f"""Generate a {scenes}-scene video script about: {topic}
Return JSON only: {{"scenes": [{{"narration": "text", "image_search": "keywords"}}]}}"""

    async with httpx.AsyncClient() as client:
        r = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}]},
            timeout=60
        )
        content = r.json()["choices"][0]["message"]["content"]
        # Extract JSON from response
        start = content.find("{")
        end = content.rfind("}") + 1
        return json.loads(content[start:end])["scenes"]

async def get_pexels_image(query: str, index: int, output_dir: Path) -> str:
    """Fetch image from Pexels (FREE)"""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={"query": query, "per_page": 5, "orientation": "landscape"}
        )
        photos = r.json().get("photos", [])
        if photos:
            url = random.choice(photos)["src"]["large2x"]
            img = await client.get(url)
            path = output_dir / f"img_{index:03d}.jpg"
            path.write_bytes(img.content)
            return str(path)
    return ""

async def generate_tts(text: str, index: int, output_dir: Path) -> str:
    """Generate voiceover using Edge TTS (FREE)"""
    path = output_dir / f"audio_{index:03d}.mp3"
    communicate = edge_tts.Communicate(text, TTS_VOICE)
    await communicate.save(str(path))
    return str(path)

def assemble_video(scenes_data: list, output_path: str):
    """Combine images and audio into video"""
    clips = []
    for img_path, audio_path in scenes_data:
        audio = AudioFileClip(audio_path)
        # Ken Burns effect
        img = ImageClip(img_path).set_duration(audio.duration)
        img = img.resize(lambda t: 1 + 0.05 * (t / audio.duration))
        img = img.set_position('center').set_audio(audio)
        clips.append(img)

    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
    return output_path

async def main(topic: str, num_scenes: int = 10):
    output_dir = Path("./outputs")
    output_dir.mkdir(exist_ok=True)
    temp_dir = output_dir / "temp"
    temp_dir.mkdir(exist_ok=True)

    print(f"🎬 Generating video about: {topic}")

    # 1. Generate script
    print("📝 Generating script...")
    scenes = await generate_script(topic, num_scenes)

    # 2. Get images and audio
    print("🖼️ Fetching images and generating voiceovers...")
    scene_files = []
    for i, scene in enumerate(scenes):
        img = await get_pexels_image(scene["image_search"], i, temp_dir)
        audio = await generate_tts(scene["narration"], i, temp_dir)
        if img and audio:
            scene_files.append((img, audio))
        print(f"  Scene {i+1}/{len(scenes)} complete")

    # 3. Assemble video
    print("🎥 Assembling video...")
    output_path = str(output_dir / f"{topic.replace(' ', '_')[:30]}.mp4")
    assemble_video(scene_files, output_path)

    print(f"✅ Video saved: {output_path}")

if __name__ == "__main__":
    import sys
    topic = sys.argv[1] if len(sys.argv) > 1 else "Amazing Facts About the Ocean"
    scenes = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    asyncio.run(main(topic, scenes))
