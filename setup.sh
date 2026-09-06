#!/bin/bash
echo "Configuring home-bot"

# Ensuring python3
python3 -m venv .venv
source .venv/bin/activate

# Create the user if not already exists
if getent passwd homebot > /dev/null 2>&1; then
    echo "Skipping user creation"
else
    echo "Creating user ..."
    useradd -m homebot &&
    passwd homebot
fi

# Configuring the user permissions
chown -R homebot:homebot /opt/home-bot

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Copy the service file
echo "Installing the service"
cp systemd/home-bot.service /etc/systemd/system/home-bot.service

# Enable the system
echo "Starting the service"
systemctl daemon-reload
systemctl enable home-bot
systemctl start home-bot

# Configuring git
git config --global --add safe.directory /opt/home-bot
