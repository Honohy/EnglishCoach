#!/bin/bash
# First-time setup on Ubuntu VPS
# Run once: bash setup.sh

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_NAME="englishcoach"
PYTHON="python3"

echo "=== EnglishCoach — First Time Setup ==="

# System packages
echo "[1/5] Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y python3 python3-pip python3-venv python3-full ffmpeg git

# Virtual environment
echo "[2/5] Creating virtual environment..."
cd "$REPO_DIR"
if [ ! -d "venv" ]; then
    $PYTHON -m venv venv || {
        echo "       venv failed, trying with --without-pip..."
        $PYTHON -m venv --without-pip venv
    }
fi
source venv/bin/activate
python -m ensurepip --upgrade 2>/dev/null || true
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "       Dependencies installed."

# .env file
echo "[3/5] Checking .env..."
if [ ! -f "$REPO_DIR/.env" ]; then
    cp "$REPO_DIR/.env.example" "$REPO_DIR/.env"
    echo ""
    echo "  !! .env file created from .env.example"
    echo "  !! Fill in your tokens before starting the bot:"
    echo "     nano $REPO_DIR/.env"
    echo ""
else
    echo "       .env already exists, skipping."
fi

# Systemd service
echo "[4/5] Creating systemd service..."
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

sudo bash -c "cat > $SERVICE_FILE" << EOF
[Unit]
Description=EnglishCoach Telegram Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$REPO_DIR
ExecStart=$REPO_DIR/venv/bin/python bot.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
echo "       Service created: $SERVICE_NAME"

# Done
echo "[5/5] Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Fill in tokens:  nano $REPO_DIR/.env"
echo "  2. Start the bot:   sudo systemctl start $SERVICE_NAME"
echo "  3. Check status:    sudo systemctl status $SERVICE_NAME"
echo "  4. View logs:       sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "  To update and restart the bot later, run: bash deploy.sh"
