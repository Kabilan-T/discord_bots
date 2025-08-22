#!/bin/bash

# Check if script is run from discord_bots directory
if [[ ! $(basename "$(pwd)") == "discord_bots" ]]; then
    echo "Please run this script from the discord_bots directory."
    exit 1
fi

# Parse argument
WITH_AUTO_UPDATE=false
if [[ "$1" == "--with-auto-update" ]]; then
    WITH_AUTO_UPDATE=true
fi


# Conditionally add cron job
if $WITH_AUTO_UPDATE; then
    echo "Checking for auto-update cron job..."
    if crontab -l 2>/dev/null | grep -q "update.bash"; then
        echo "Cron job already exists."
    else
        current_directory=$(pwd)
        mkdir -p "$current_directory/logs"
        # Add the cron job to run the update.bash script every 6 hours
        (crontab -l 2>/dev/null; echo "0 */6 * * * bash $current_directory/update.bash >> $current_directory/logs/update.log 2>&1") | crontab -
        echo "Cron job added to run update.bash every 6 hours."
    fi
else
    echo "Skipping auto-update setup. Run './setup.bash --with-auto-update' if you want to enable it."
fi

# Check if runtime.txt file exists
if [ ! -f "runtime.txt" ]; then
    echo "runtime.txt not found. Please create runtime.txt and specify the Python version."
    exit 1
fi

# Read Python version from runtime.txt
python_version=$(cat runtime.txt)

# Check if virtual environment exists
if conda env list | grep -q discord_bots_env; then
    echo "Virtual environment 'discord_bots_env' already exists."
else
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

# Install dependencies
echo "Installing dependencies..."
pip install --no-cache-dir -r requirements.txt --use-deprecated=legacy-resolver

echo "Setup complete. Please fill in your bot tokens in tokens.sh and then run the bot using run.bash."

exit 0