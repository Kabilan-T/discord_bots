#!/bin/bash

# Pull recent changes from the remote repository
git pull origin master

# Check if there are any changes
if [ $? -eq 0 ]; then
    echo "$(date) - Changes detected, running setup.bash"
    # Run setup.bash
    bash setup.bash
else
    echo "$(date) - No changes detected"
fi