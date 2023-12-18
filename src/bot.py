# Main file for the bot

import os
import yaml
import discord
from discord.ext import commands

# Load discord token from config file
config = yaml.load(open(os.path.join(os.path.dirname(__file__), "config", "bot.yml"), "r"), Loader=yaml.FullLoader)
BotName = config["name"]
BotUsername = config["username"]
BotToken = config["token"]

# Create a discord bot
intents=discord.Intents.default()
intents.members = True
intents.presences = True
intents.message_content = True
bot = commands.Bot(command_prefix='$$', intents=intents)

@bot.command(name='hello', help='Responds with a greeting')
async def hello(ctx):
    await ctx.send('Hello World! I am ' + BotName + '. I\'m here to help you!')


@bot.command(name='create-channel')
@commands.has_role('admin')
async def create_channel(ctx, channel_name='real-python'):
    guild = ctx.guild
    existing_channel = discord.utils.get(guild.channels, name=channel_name)
    if not existing_channel:
        print(f'Creating a new channel: {channel_name}')
        await guild.create_text_channel(channel_name)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found. Use `$$help` for a list of available commands.")
    elif isinstance(error, commands.MissingRole):
        await ctx.send("You do not have the required role to use this command.")
    else:
        print(f"An error occurred: {error}")


bot.run(BotToken)



