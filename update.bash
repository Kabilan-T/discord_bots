#!/bin/bash

# Change directory to the location of the script
SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"
cd "$SCRIPTPATH" || exit

echo
echo "--------------------------------------------------"
echo "Time - $(date)"

# Update the repository
echo "Updating the repository ...."
GIT_RESET_OUTPUT=$(git reset --hard origin/main) || { echo "Error resetting repository. Exiting..."; exit 1; }
GIT_PULL_OUTPUT=$(git pull origin main) || { echo "Error pulling from repository. Exiting..."; exit 1; }

# Check if there were actual changes pulled
if [[ $GIT_PULL_OUTPUT == *"Already up to date."* ]]; then
    echo "No changes detected."
else
    echo "Changes detected..."
    echo "Last commit: $(git log -1 --pretty=format:"%h : '%s' - %ci" HEAD)"

    # Check if requirements.txt has changed in the most recent commit
    echo "Checking if 'requirements.txt' has changed..."
    HAS_REQUIREMENTS_CHANGED=$(git diff-tree --no-commit-id --name-only -r HEAD | grep -c "requirements.txt")
    if [ $HAS_REQUIREMENTS_CHANGED -eq 1 ]; then
        echo "'requirements.txt' has changes in the most recent commit."
        echo "Updating package dependencies..."
        # Activate virtual environment
        echo "Activating virtual environment (discord_bots_env)..."
        eval "$(conda shell.bash hook)"
        conda activate discord_bots_env
        # Install dependencies
        echo "Installing dependencies..."
        pip install --no-cache-dir -r requirements.txt --use-deprecated=legacy-resolver
        echo "Dependencies updated. Please restart the bot or reload the cogs."
    else
        echo "No changes detected in 'requirements.txt'."
    fi
fi

echo "--------------------------------------------------"
echo
