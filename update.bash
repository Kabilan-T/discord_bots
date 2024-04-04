#!/bin/bash

# Change directory to the location of the script
SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"
cd "$SCRIPTPATH"

# Pull recent changes from the remote repository
git pull origin main

# Check if there are any changes
if [ $? -eq 0 ]; then
    echo "$(date) - Changes detected, running setup.bash"
    # Run setup.bash
    bash setup.bash
else
    echo "$(date) - No changes detected"
fi