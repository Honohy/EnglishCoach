#!/bin/bash
# Update from git and restart the bot
# Run anytime: bash deploy.sh

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_NAME="englishcoach"

echo "=== EnglishCoach — Deploy ==="

# Git pull
echo "[1/3] Pulling latest code from git..."
cd "$REPO_DIR"
git pull
echo "       Done."

# Install/update dependencies
echo "[2/3] Updating dependencies..."
source venv/bin/activate
pip install -r requirements.txt -q
echo "       Done."

# Restart service
echo "[3/3] Restarting bot..."
sudo systemctl restart "$SERVICE_NAME"
sleep 2

STATUS=$(sudo systemctl is-active "$SERVICE_NAME")
if [ "$STATUS" = "active" ]; then
    echo "       Bot is running. Status: $STATUS"
else
    echo "       WARNING: Bot status is '$STATUS'"
    echo "       Check logs: sudo journalctl -u $SERVICE_NAME -n 30"
fi

echo ""
echo "=== Done! ==="
echo "  Logs: sudo journalctl -u $SERVICE_NAME -f"
