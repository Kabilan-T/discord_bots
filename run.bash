#!/bin/bash

source tokens.sh

# Run the bot
python3 src/auto.py &
python3 src/eve.py &
python3 src/mo.py 
