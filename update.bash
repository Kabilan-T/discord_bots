#!/bin/bash

# Change directory to the location of the script
SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"
cd "$SCRIPTPATH" || exit

echo
echo "--------------------------------------------------"
echo "Time - $(date)"

# Pull recent changes from the remote repository
echo "----- Updating repository -----"
PULL_OUTPUT=$(git pull origin main)

# Check if there were actual changes pulled
if [[ $PULL_OUTPUT == *"Already up to date."* ]]; then
    echo "--- No changes detected ---"
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

# check if the date is 26 Oct 2024 and apply temporary patch for instaloader
if [[ $(date +%Y-%m-%d) == "2024-10-26" ]]; then
    # Convert the current time to Eastern Time (ET)
    CURRENT_HOUR_ET=$(TZ="America/New_York" date +%H)
        
    if [[ $CURRENT_HOUR_ET -ge 12 && $CURRENT_HOUR_ET -lt 23 ]]; then
        echo "----- Temporary patch for instaloader - Applies only on 26 Oct 2024 -----"
        # Temporary patch for instaloader --- remove when the issue is fixed
        echo "Applying temporary instaloader patch..."
        PATCH_URL="https://github.com/user-attachments/files/17509648/instaloader.zip"
        SITE_PACKAGES_DIR=$(python -c "import site; print(site.getsitepackages()[0])")
        INSTALOADER_PATH="$SITE_PACKAGES_DIR/instaloader"
        
        # Remove existing instaloader package and apply patch
        if [ -d "$INSTALOADER_PATH" ]; then
            echo "Removing old instaloader package..."
            rm -rf "$INSTALOADER_PATH"
        fi
        
        echo "Downloading and unzipping patch..."
        curl -L -o instaloader.zip "$PATCH_URL"
        unzip -o instaloader.zip -d "$SITE_PACKAGES_DIR"
        rm instaloader.zip
        echo "Instaloader patch applied successfully."
        ##### --- Temporary patch for instaloader ends here --- #####
    else
        echo "Patch time window not met (12:00-23:00 ET). Patch will not be applied."
    fi
fi
echo "--------------------------------------------------"
echo
