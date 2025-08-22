# Discord Bots

This project contains multiple Discord bots written in Python using the `discord.py` library. The bots are designed to perform various tasks and are tailored to the specific needs of our own Discord server called "Axiom". The server theme is based on the movie "WALL-E" and the bots are named to resemble the characters from the movie. The functionality of the bots is modular and can be easily extended to include more features. Even new bots can be added to the project with ease.

## Bots

The following bots are currently available in the project:

### 1. AUTO 

AUTO is the auto-pilot for the ship. It's job is to ensure smooth operation of the server by providing various administrative tools and features. The main functionalities include:
- Moderation tools for handling member behavior.
- Utilities for managing messages and voice channels.
- Role management, including defaults and reaction roles.
- Announcements such as welcomes, farewells, and daily highlights.
Main file: [`auto.py`](src/auto.py)

### 2. EVE

EVE is the explorer probe of the ship, designed to make the community more engaging and entertaining.
The main functionalities include:
- Voice interactions with greetings, text-to-speech, and customization.
- Watchlist management for movies and shows with announcements.
- Meme collection and template management for fun interactions.
Main file: [`eve.py`](src/eve.py)

### 3. M-O

M-O is the clean-up specialist. Give it a task and it will make sure the server stays tidy and organized. The main functionalities include:
- Radio streaming in voice channels with station management.
- Instagram integration. Ask M-O to watch a channel. It will fetch media content, bio, info, and posts from the instagram links posted in the channel.
Main file: [`mo.py`](src/mo.py)

### 4. GO-4

GO-4 is the security and assistant officer, responsible for knowledge, assistance, and playful features. It can hold dialogues with users and provide help using LLMs. While playful, it also grants administrators some powerful and unique capabilities. The main functionalities include:

- Conversational interactions powered by language models.
- Posting a Thirukkural daily, with access to Kurals in Tamil and English.
- Pop-culture-inspired commands through the CosmicCon module.
Main file: [`go4.py`](src/go4.py)

## Usage

To use the bots in your own server, you need to create a Discord bot and get the token. The following link provides the instructions to create a Discord bot and get the token: [Discord Bot](https://discordpy.readthedocs.io/en/stable/discord.html)

The tokens are secret and should not be shared with anyone. The tokens are sourced as environment variables and are used in the code to authenticate the bot with the Discord server. 

Create a `tokens.sh` file in the root directory of the project and add the following lines to the file.

```
export AUTO_BOT_TOKEN="<Enter auto bot token here>"

export EVE_BOT_TOKEN="<Enter eve bot token here>"

export MO_BOT_TOKEN="<Enter mo bot token here>"

export GO4_BOT_TOKEN="<Enter go4 bot token here>"
```

Follow the instructions in the [Installation](#installation) section to create the virtual environment and install the required packages.

To start the bot's execution, a `run.bash` script is provided in the repository. It takes the bot name as an argument and starts the bot execution. The script will activate the virtual environment, source the token file, and run the Python script of the bot. The command to run the script is as follows.
```
bash run.bash <bot_name>
```
or make the script executable and run the script.
```
chmod +x run.bash
./run.bash <bot_name>
```
Replace `<bot_name>` with the bot name you want to start. The bot names are `auto`, `eve`, and `mo`. Open three terminals in the root directory of the project and run the following commands.

* ```bash run.bash auto```: Starts the AUTO bot.
* ```bash run.bash eve```: Starts the EVE bot.
* ```bash run.bash mo```: Starts the MO bot.
* ```bash run.bash go4```: Starts the GO4 bot (if implemented).

The bots will start executing and you can see the logs in the terminal.

To stop a bot execution, press `Ctrl + C` in the terminal where the bot is running.

Note: If you don't have `tokens.sh` file in the root directory, `run.bash` script will create a template file for you. You need to enter the bot tokens in the file and run the `run.bash` script again.

## Installation

1. Clone the repository to your local machine.

```
git clone https://github.com/Kabilan-T/discord_bots.git
```

2. Install miniconda or anaconda to create a virtual environment. Use the following link for installation instructions: [Miniconda](https://conda.io/projects/conda/en/latest/index.html) or use the following command to install Miniconda.

```
sudo apt-get update
sudo apt-get install wget
mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm -rf ~/miniconda3/miniconda.sh
~/miniconda3/bin/conda init bash
source ~/.bashrc
```

3. Create the virtual environment and install the required packages. To ease the installation process, a `setup.bash` script is provided in the repository. Run the following command.
    
```
bash setup.bash
```
optional: `--with-auto-update` flag to enable automatic updates (cron job to run `update.bash` every 6 hours, which fetches the latest changes from the repository and applies them).

```
bash setup.bash --with-auto-update
```



Credits: [Vijhay Anandd](https://github.com/vijayanandrp)  for [Thirukkural Dataset](https://github.com/vijayanandrp/Thirukkural-Tamil-Dataset)
