#!/bin/bash

# Change directory to the location of the script
SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"
cd "$SCRIPTPATH" || exit

echo
echo "--------------------------------------------------"
echo "Time - $(date)"

# Log current git status for troubleshooting
echo "----- Checking repository status -----"
git status

# Update the repository ignoring local changes
echo "----- Updating repository (force pull) -----"
git fetch origin
git reset --hard origin/main
PULL_OUTPUT=$(git pull origin main)

# Check if there were actual changes pulled
if [[ $PULL_OUTPUT == *"Already up to date."* ]]; then
    echo "--- No changes detected ----"
else
    echo "--- Changes detected ---"
    echo "Recent commit: $(git log -1 --pretty=format:"%h : '%s' - %ci" HEAD)"
    echo "---------- Update package dependencies ----------"
    # Activate virtual environment
    eval "$(conda shell.bash hook)"
    conda activate discord_bots_env
    echo "Virtual environment 'discord_bots_env' activated."
    # Install dependencies
    echo "Installing dependencies..."
    pip install --no-cache-dir -r requirements.txt --use-deprecated=legacy-resolver
    echo "---------- Update package dependencies complete ----------"
fi

# Update the existing crontab to run every hour instead of every 6 hours
echo "----- Adjusting crontab frequency to every hour -----"
current_directory=$(pwd)
(crontab -l | sed "/update.bash/c\0 * * * * bash $current_directory/update.bash >> $current_directory/logs/update.log") | crontab -

echo "--------------------------------------------------"
echo
