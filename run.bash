#!/bin/bash

# Check if script is run from discord_bots directory
if [[ ! $(basename "$(pwd)") == "discord_bots" ]]; then
    echo "Please run this script from the discord_bots directory."
    exit 1
fi

# Check if correct number of arguments are provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <bot_name>"
    exit 1
fi

# Bot name provided as argument
bot_name=$1

# Check if tokens.sh file exists
if [ ! -f "tokens.sh" ]; then
    echo "tokens.sh not found. Creating a template..."
    # Create tokens.sh file with template
    cat << EOF > tokens.sh
#!/bin/bash

# Please fill in your bot tokens below

export AUTO_BOT_TOKEN="<Enter auto bot token here>"

export EVE_BOT_TOKEN="<Enter eve bot token here>"

export MO_BOT_TOKEN="<Enter mo bot token here>"

EOF
    echo "Template created in tokens.sh. Please fill in your bot tokens and then rerun the script."
    exit 0
fi

# Activate virtual environment
eval "$(conda shell.bash hook)"
conda activate discord_bots_env
echo "Virtual environment 'discord_bots_env' activated."

# Source token file
source tokens.sh

# Run the corresponding bot based on provided argument
case "$bot_name" in
    "auto")
        python3 src/auto.py
        ;;
    "eve")
        python3 src/eve.py
        ;;
    "mo")
        python3 src/mo.py
        ;;
    *)
        echo "Invalid bot name. Available bots: auto, eve, mo"
        exit 1
        ;;
esac

exit 0
