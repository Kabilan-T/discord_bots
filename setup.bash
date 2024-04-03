#!/bin/bash

# Check if script is run from discord_bots directory
if [[ ! $(basename "$(pwd)") == "discord_bots" ]]; then
    echo "Please run this script from the discord_bots directory."
    exit 1
fi

# Check if update.bash exists
if crontab -l | grep -q "update.bash"; then
    echo "Cron job already exists."
else
    current_directory=$(pwd)
    # Add the cron job to run the update.sh script every 12 hours
    (crontab -l ; echo "0 */12 * * * bash $current_directory/update.bash" >> logs/update.log) | crontab -
    echo "Cron job added to run the update.sh script every 12 hours."
fi

# Check if runtime.txt file exists
if [ ! -f "runtime.txt" ]; then
    echo "runtime.txt not found. Please create runtime.txt and specify the Python version."
    exit 1
fi

# Read Python version from runtime.txt
python_version=$(cat runtime.txt)

# Check if virtual environment exists
if ! conda env list | grep -q discord_bots_env; then
    echo "Creating virtual environment with Python $python_version..."
    # Create virtual environment with specified Python version
    conda create -n discord_bots_env python="$python_version"
fi

# Activate virtual environment
eval "$(conda shell.bash hook)"
conda activate discord_bots_env
echo "Virtual environment 'discord_bots_env' activated."

# install ffmpeg if not installed
if ! command -v ffmpeg &> /dev/null; then
    echo "ffmpeg not found. Installing ffmpeg..."
    conda install -c conda-forge ffmpeg
fi

# Install dependencies
echo "Updating pip..."
pip install --upgrade pip
echo "Installing dependencies..."
pip install -r requirements.txt --use-deprecated=legacy-resolver

echo "Setup complete. Please fill in your bot tokens in tokens.sh and then run the bot using run.bash."

exit 0