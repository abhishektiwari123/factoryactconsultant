# ASTRONOVA AI Video Production System

A complete AI-powered video production system for creating:
- Long-form faceless videos (documentary/explainer style)
- LoFi music videos
- Sleep/ambient videos (8+ hours)
- Viral shorts/reels

## Quick Start

```bash
# 1. Set up environment
cp .env.example .env
# Edit .env with your API keys

# 2. Install dependencies
cd scripts && pip install -r requirements.txt

# 3. Run the system
./start.sh
```

## FREE API Keys Required

| Service | URL | Cost | Purpose |
|---------|-----|------|---------|
| Groq | https://console.groq.com/keys | FREE (14,400 req/day) | AI script generation |
| Pexels | https://www.pexels.com/api/ | FREE (unlimited) | Stock images/videos |

### Optional (Cheap) APIs

| Service | URL | Cost | Purpose |
|---------|-----|------|---------|
| DeepSeek | https://platform.deepseek.com/ | $0.14/1M tokens | Backup AI |
| Together.ai | https://together.ai | $0.0013/image | AI image gen |

## Directory Structure

```
astronova-video/
├── moneyprinter/       # MoneyPrinterTurbo installation
├── n8n/                # n8n workflow automation
│   └── docker-compose.yml
├── scripts/            # Custom video generators
│   ├── generate_video.py    # Long-form videos
│   ├── generate_lofi.py     # LoFi music videos
│   ├── generate_sleep.py    # Sleep/ambient videos
│   └── generate_shorts.py   # Viral shorts/reels
├── outputs/            # Generated videos
├── resources/
│   ├── fonts/          # Custom fonts
│   └── music/          # Royalty-free music
├── .env                # API keys
├── start.sh            # Launcher script
└── README.md
```

## Video Generators

### 1. Long-Form Videos (`generate_video.py`)

Creates documentary-style videos with AI narration.

```bash
python generate_video.py "5 Mind-Blowing Facts About Space" 10
#                         ^topic                           ^scenes
```

### 2. LoFi Music Videos (`generate_lofi.py`)

Creates aesthetic LoFi background videos.

```bash
python generate_lofi.py music.mp3 "cozy coffee shop rain" 2
#                       ^audio    ^theme                  ^hours
```

Available themes:
- `cozy coffee shop window rain`
- `anime bedroom night city view`
- `study desk lamp books aesthetic`
- `rainy window city lights night`
- `sunset bedroom cozy aesthetic`
- `japanese street night aesthetic`

### 3. Sleep/Ambient Videos (`generate_sleep.py`)

Creates ultra-long relaxation videos.

```bash
python generate_sleep.py rain 8 ambient.mp3
#                        ^theme ^hours ^audio(optional)
```

Available themes: `rain`, `fireplace`, `ocean`, `forest`, `snow`, `stars`, `underwater`

### 4. Viral Shorts (`generate_shorts.py`)

Creates engaging 30-60 second vertical videos.

```bash
python generate_shorts.py "productivity hacks" tips
#                         ^topic               ^format
```

Formats: `facts`, `tips`, `mistakes`, `ranking`

## Web Interfaces

After running `./start.sh`:

| Service | URL | Credentials |
|---------|-----|-------------|
| MoneyPrinterTurbo | http://localhost:8501 | - |
| n8n Workflows | http://localhost:5678 | admin / astronova2024 |

## System Requirements

- Python 3.11+
- FFmpeg
- ImageMagick
- Docker & Docker Compose
- Node.js 18+ (for n8n)

### Install Dependencies (Ubuntu/Debian)

```bash
sudo apt update && sudo apt install -y \
    ffmpeg imagemagick python3.11 python3.11-venv \
    nodejs npm docker.io docker-compose git

# Fix ImageMagick policy
sudo sed -i 's/rights="none" pattern="@\*"/rights="read|write" pattern="@*"/' \
    /etc/ImageMagick-6/policy.xml 2>/dev/null || true
```

## n8n Workflow Automation

Use n8n to automate video production:

1. Schedule daily video generation
2. Auto-upload to YouTube/TikTok
3. Trigger videos based on trending topics
4. Batch process multiple videos

Example workflow ideas:
- Daily "Facts of the Day" video
- Weekly LoFi compilation
- Trending topic shorts generator

## Tips for Viral Content

### Shorts/Reels
- Keep videos 30-60 seconds
- Strong hook in first 3 seconds
- Use trending audio/topics
- Include CTA (follow, save, share)

### Long-Form
- 8-15 minute sweet spot
- Compelling thumbnails
- SEO-optimized titles
- Consistent posting schedule

### LoFi/Sleep
- Longer = better for watch time
- Upload during peak sleep hours
- Use descriptive titles for search
- Create playlists

## Troubleshooting

### "No API key" errors
Make sure `.env` file exists and contains valid keys.

### FFmpeg errors
```bash
sudo apt install ffmpeg
```

### ImageMagick policy errors
```bash
sudo sed -i 's/rights="none"/rights="read|write"/g' /etc/ImageMagick-6/policy.xml
```

### Docker permission errors
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

## License

MIT License - Use freely for personal and commercial projects.
