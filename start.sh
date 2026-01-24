#!/bin/bash
echo "🚀 Starting ASTRONOVA Video System..."
export $(cat .env | xargs)

# Start MoneyPrinterTurbo
cd moneyprinter && source venv/bin/activate
python webui/Main.py &

# Start n8n
cd ../n8n && docker-compose up -d

echo "
✅ System Running!

📍 Access:
  MoneyPrinterTurbo: http://localhost:8501
  n8n Workflows:     http://localhost:5678 (admin/astronova2024)

🎬 Quick Generate:
  cd scripts && python generate_video.py 'Your Topic Here' 10
"
