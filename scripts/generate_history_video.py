#!/usr/bin/env python3
"""
"100 साल पहले" style long-form video generator (Chulha Aangan).

Turns an episode folder containing scenes.json into a finished 1080p video:
Hindi AI narration + AI-generated period images + Ken Burns motion + title cards + music.

Usage:
    python generate_history_video.py ../chulha_aangan/ep01_diwali_1926
    python generate_history_video.py EPISODE_DIR --images together --music bg.mp3
    python generate_history_video.py EPISODE_DIR --images manual     # use your own images
    python generate_history_video.py EPISODE_DIR --placeholder       # test timing, no network

Every step is cached in EPISODE_DIR/work/, so re-running only redoes what is missing.
To replace a bad image, delete (or overwrite) work/images/seg_XX_YY.jpg and run again.
"""
import argparse
import asyncio
import base64
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

FPS = 25
W, H = 1920, 1080

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "C:/Windows/Fonts/georgiab.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        sys.exit(f"Command failed: {' '.join(map(str, cmd))}\n{r.stderr[-2000:]}")
    return r.stdout


def duration(path: Path) -> float:
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=nw=1:nk=1", str(path)])
    return float(out.strip())


def expand(prompt: str, characters: dict) -> str:
    return re.sub(r"\{(\w+)\}", lambda m: characters.get(m.group(1), m.group(0)), prompt)


# ---------------------------------------------------------------- narration

async def tts_edge(text, voice, rate, pitch, path: Path):
    import edge_tts  # pip install edge-tts
    await edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).save(str(path))


def make_audio(seg, cfg, path: Path, placeholder: bool):
    if path.exists():
        return
    if placeholder:
        # ~2.3 Hindi words per second at the chosen narration rate
        secs = max(4.0, len(seg["narration"].split()) / 2.3)
        run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono",
             "-t", f"{secs:.2f}", "-q:a", "9", str(path)])
        return
    for attempt in range(4):
        try:
            asyncio.run(tts_edge(seg["narration"], cfg["voice"], cfg["voice_rate"],
                                 cfg["voice_pitch"], path))
            return
        except Exception as e:  # network hiccups are common, retry
            print(f"    TTS retry {attempt + 1}: {e}")
            time.sleep(2 ** attempt)
    sys.exit(f"TTS failed for segment {seg['id']}")


# ---------------------------------------------------------------- images

def fetch(url, data=None, headers=None, timeout=180):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def image_pollinations(prompt, negative, seed, path: Path):
    q = urllib.parse.quote(prompt)
    url = (f"https://image.pollinations.ai/prompt/{q}?width={W}&height={H}"
           f"&seed={seed}&nologo=true&model=flux&negative={urllib.parse.quote(negative)}")
    path.write_bytes(fetch(url))


def image_together(prompt, negative, seed, path: Path):
    key = os.environ["TOGETHER_API_KEY"]
    body = json.dumps({
        "model": os.getenv("TOGETHER_MODEL", "black-forest-labs/FLUX.1-schnell"),
        "prompt": prompt, "width": 1344, "height": 768, "steps": 4, "n": 1,
        "seed": seed, "response_format": "b64_json",
    }).encode()
    out = json.loads(fetch("https://api.together.xyz/v1/images/generations", body,
                           {"Authorization": f"Bearer {key}",
                            "Content-Type": "application/json"}))
    path.write_bytes(base64.b64decode(out["data"][0]["b64_json"]))


def image_placeholder(text, idx, path: Path):
    random.seed(idx)
    color = "0x%02x%02x%02x" % (random.randint(80, 200), random.randint(50, 140),
                                random.randint(20, 80))
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c={color}:s={W}x{H}",
         "-frames:v", "1", str(path)])


def make_image(prompt, cfg, path: Path, mode: str, seed: int):
    if path.exists():
        return
    if mode == "manual":
        return  # reported as missing later
    full = f"{prompt}, {cfg['style']}"
    for attempt in range(5):
        try:
            if mode == "placeholder":
                image_placeholder(prompt, seed, path)
            elif mode == "together":
                image_together(full, cfg["negative"], seed, path)
            else:
                image_pollinations(full, cfg["negative"], seed, path)
            return
        except Exception as e:
            print(f"    image retry {attempt + 1}: {e}")
            time.sleep(3 * (attempt + 1))
    print(f"    !! could not generate {path.name} - add it manually and re-run")


# ---------------------------------------------------------------- video

MOTIONS = [
    # slow zoom in, centred
    ("1+0.15*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    # slow zoom out, centred
    ("1.15-0.15*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    # pan left -> right
    ("1.12", "(iw-iw/zoom)*on/{n}", "ih/2-(ih/zoom/2)"),
    # pan right -> left
    ("1.12", "(iw-iw/zoom)*(1-on/{n})", "ih/2-(ih/zoom/2)"),
]


def ken_burns(img: Path, secs: float, motion: int, out: Path):
    n = max(1, round(secs * FPS))
    z, x, y = (e.format(n=n) for e in MOTIONS[motion % len(MOTIONS)])
    vf = (f"scale={W * 2}:{H * 2}:force_original_aspect_ratio=increase,"
          f"crop={W * 2}:{H * 2},"
          f"zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={FPS},"
          f"setsar=1,format=yuv420p")
    run(["ffmpeg", "-y", "-i", str(img), "-vf", vf, "-frames:v", str(n),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", str(out)])


def find_font(user_font):
    for f in ([user_font] if user_font else []) + FONT_CANDIDATES:
        if f and Path(f).exists():
            return f
    return None


def drawtext_filters(cards, font):
    if not cards or not font:
        return ""
    font = font.replace("\\", "/").replace(":", r"\:")
    parts = []
    for c in cards:
        s, e = c["start"], c["end"]
        alpha = f"if(lt(t,{s}+0.6),(t-{s})/0.6,if(gt(t,{e}-0.6),({e}-t)/0.6,1))"
        parts.append(
            f"drawtext=fontfile='{font}':text='{c['text']}':fontsize=84:fontcolor=white:"
            f"shadowcolor=black@0.7:shadowx=3:shadowy=3:x=(w-text_w)/2:y=h*0.72:"
            f"enable='between(t,{s},{e})':alpha='{alpha}'")
    return ",".join(parts)


def build_segment(seg, shots, audio: Path, work: Path, cards, font, motion_start):
    out = work / "segments" / f"seg_{seg['id']:02d}.mp4"
    newest_input = max(f.stat().st_mtime for f in [audio, *shots])
    if out.exists() and out.stat().st_mtime >= newest_input:
        return out  # up to date; replacing an image or audio file re-renders it
    total = duration(audio) + 0.35  # small breath between segments
    each = total / len(shots)
    clips = []
    for i, img in enumerate(shots):
        clip = work / "clips" / f"{img.stem}.mp4"
        ken_burns(img, each, motion_start + i, clip)
        clips.append(clip)
    lst = work / "clips" / f"seg_{seg['id']:02d}.txt"
    lst.write_text("".join(f"file '{c.resolve().as_posix()}'\n" for c in clips))
    vf = drawtext_filters(cards, font) or "null"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(audio),
         "-filter_complex", f"[0:v]{vf}[v];[1:a]apad,atrim=0:{total:.3f},"
         f"aresample=48000[a]",
         "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", str(out)])
    return out


def final_mix(segments, music, out: Path, work: Path, music_vol: float):
    lst = work / "segments.txt"
    lst.write_text("".join(f"file '{s.resolve().as_posix()}'\n" for s in segments))
    joined = work / "joined.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
         str(joined)])
    total = duration(joined)
    fade = f"fade=t=in:st=0:d=1.5,fade=t=out:st={total - 2:.2f}:d=2"
    if music:
        run(["ffmpeg", "-y", "-i", str(joined), "-stream_loop", "-1", "-i", str(music),
             "-filter_complex",
             f"[0:v]{fade}[v];"
             f"[1:a]volume={music_vol},afade=t=out:st={total - 4:.2f}:d=4[m];"
             f"[0:a][m]amix=inputs=2:duration=first:normalize=0[a]",
             "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}",
             "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)])
    else:
        run(["ffmpeg", "-y", "-i", str(joined), "-vf", fade,
             "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
             "-c:a", "copy", "-movflags", "+faststart", str(out)])
    return total


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("episode", type=Path, help="folder with scenes.json")
    ap.add_argument("--images", choices=["pollinations", "together", "manual"],
                    default="pollinations",
                    help="pollinations = free, no key; together = needs TOGETHER_API_KEY; "
                         "manual = you put your own images in work/images/")
    ap.add_argument("--placeholder", action="store_true",
                    help="coloured frames + silent audio, to test the pipeline offline")
    ap.add_argument("--music", type=Path, help="background music file (loops)")
    ap.add_argument("--music-volume", type=float, default=0.12)
    ap.add_argument("--font", help="TTF font for the title cards")
    ap.add_argument("--seed", type=int, default=1926)
    args = ap.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found - install it first (https://ffmpeg.org/download.html)")

    cfg = json.loads((args.episode / "scenes.json").read_text(encoding="utf-8"))
    chars = cfg.get("characters", {})
    work = args.episode / "work"
    for d in ("audio", "images", "clips", "segments"):
        (work / d).mkdir(parents=True, exist_ok=True)
    mode = "placeholder" if args.placeholder else args.images

    # prompts.txt is handy for generating images by hand in Leonardo / Ideogram / Meta AI
    with open(args.episode / "prompts.txt", "w", encoding="utf-8") as f:
        for seg in cfg["segments"]:
            for j, p in enumerate(seg["shots"], 1):
                f.write(f"seg_{seg['id']:02d}_{j:02d}.jpg | {expand(p, chars)}, "
                        f"{cfg['style']}\n")

    print(f"🎬 {cfg['title']}")
    plan = []
    missing = []
    for seg in cfg["segments"]:
        sid = seg["id"]
        print(f"  [{sid:02d}/{len(cfg['segments'])}] {seg['section']}")
        audio = work / "audio" / f"seg_{sid:02d}.mp3"
        make_audio(seg, cfg, audio, args.placeholder)
        imgs = []
        for j, p in enumerate(seg["shots"], 1):
            img = work / "images" / f"seg_{sid:02d}_{j:02d}.jpg"
            make_image(expand(p, chars), cfg, img, mode, args.seed + sid * 100 + j)
            if img.exists():
                imgs.append(img)
            else:
                missing.append(img.name)
        plan.append((seg, audio, imgs))

    if missing:
        sys.exit("Missing images (see prompts.txt for their prompts):\n  "
                 + "\n  ".join(missing) + f"\nPut them in {work / 'images'} and re-run.")

    font = find_font(args.font)
    if cfg.get("title_cards") and not font:
        print("  (no font found - title cards skipped; pass --font path/to/font.ttf)")

    print("🎥 Rendering segments...")
    segments, motion = [], 0
    for seg, audio, imgs in plan:
        cards = [c for c in cfg.get("title_cards", []) if c["segment"] == seg["id"]]
        segments.append(build_segment(seg, imgs, audio, work, cards, font, motion))
        motion += len(imgs)

    out = args.episode / f"{args.episode.name}{'_preview' if args.placeholder else ''}.mp4"
    total = final_mix(segments, args.music, out, work, args.music_volume)
    print(f"✅ {out}  ({int(total // 60)}:{int(total % 60):02d})")


if __name__ == "__main__":
    main()
