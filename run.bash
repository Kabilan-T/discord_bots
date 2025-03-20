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

# Activate the virtual environment
eval "$(conda shell.bash hook)"
conda activate discord_bots_env

# Check if the Conda environment is activated
if [[ -z "$CONDA_PREFIX" ]]; then
    echo "Failed to activate Conda environment 'discord_bots_env'. Exiting."
    exit 1
fi

echo "Virtual environment 'discord_bots_env' activated."

# Read Python version from runtime.txt
python_version=$(cat runtime.txt)

# Check if the desired Python version exists and is available in the system
python_path=$(which "python$python_version")

if [ -z "$python_path" ]; then
    echo "Python $python_version is not installed. Please install the required version."
    exit 1
fi

# Source token file
source tokens.sh

# Run the corresponding bot based on the provided argument
case "$bot_name" in
    "auto")
        "$python_path" src/auto.py
        ;;
    "eve")
        "$python_path" src/eve.py
        ;;
    "mo")
        "$python_path" src/mo.py
        ;;
    *)
        echo "Invalid bot name. Available bots: auto, eve, mo"
        exit 1
        ;;
esac

exit 0
