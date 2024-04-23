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
    echo "---------- Running Setup ----------"
    bash setup.bash
    echo "---------- Setup is done ----------"
fi

echo "--------------------------------------------------"
echo
