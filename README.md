# Discord Bots

This project contains multiple Discord bots written in Python using the `discord.py` library. The bots are designed to perform various tasks and are tailored to the specific needs of our own Discord server called "Axiom". The server theme is based on the movie "WALL-E" and the bots are named to resemble the characters from the movie. The functionality of the bots is modular and can be easily extended to include more features. Even new bots can be added to the project with ease.

## Bots

The following bots are currently available in the project:

### 1. AUTO 

This bot is designed to perform managing tasks such as sending welcome messages, assigning roles, and moderating the server by warning, muting, and kicking users. \
Main file: [`auto.py`](src/auto.py)

### 2. EVE

This bot is designed for fun and entertainment purposes. It can play a game of BINGO with the users in the server and it can join the voice channel and greet the users who join the channel. With Google text-to-speech, it can also read out the user messages in the voice channel aiding the users who are unable to talk in the voice channel. \
Main file: [`eve.py`](src/eve.py)

### 3. M-O

This bot is designed to perform utility tasks on the server. Right now, it can fetch the media content from Instagram and post it on the server. More features can be added to this bot to perform more utility tasks. \
Main file: [`mo.py`](src/mo.py)

## Usage

To use the bots in your own server, you need to create a Discord bot and get the token. The following link provides the instructions to create a Discord bot and get the token: [Discord Bot](https://discordpy.readthedocs.io/en/stable/discord.html)

The tokens are secret and should not be shared with anyone. The tokens are sourced as environment variables and are used in the code to authenticate the bot with the Discord server. 

Create a `tokens.sh` file in the root directory of the project and add the following lines to the file.

```
export AUTO_BOT_TOKEN="<Enter auto bot token here>"

export EVE_BOT_TOKEN="<Enter eve bot token here>"

export MO_BOT_TOKEN="<Enter mo bot token here>"
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
or make the script executable and run the script.

```
chmod +x setup.bash
./setup.bash
```


Credits: [Vijhay Anandd](https://github.com/vijayanandrp)  for [Thirukkural Dataset](https://github.com/vijayanandrp/Thirukkural-Tamil-Dataset)