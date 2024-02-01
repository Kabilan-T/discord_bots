#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Discord bot class definition'''

#-------------------------------------------------------------------------------

import os
import yaml
import discord
from discord.ext import commands
from src.log import BotLogger
    
class MyBot(commands.Bot):
    def __init__(self):
        # Load discord bot config
        config = yaml.load(open(os.path.join(os.path.dirname(__file__), "config", "bot.yml"), "r"), Loader=yaml.FullLoader)
        self.name = config["name"]
        self.username = config["username"]
        self.prefix = config["default_prefix"]
        self.client_id = config["client_id"]
        self.voice = config["voice"]
        self.extensions_to_load = config["extensions"]
        self.log_channel_id = config["log_channel_id"]
        # Setup logging
        self.logger = BotLogger()
        self.logger.info(f"Loaded config for {self.name}", send_to_log_channel=False)
        # Create discord bot
        super().__init__(description="Discord bot : "+self.name,
                         command_prefix=self.prefix, 
                         intents=discord.Intents.all(),
                         help_command=None,
                         application_id=self.client_id)
        
    async def setup_hook(self):
        # Load cogs
        for extension in self.extensions_to_load:
            if os.path.isfile(os.path.join(os.path.dirname(__file__), "cogs", extension+".py")):
                try:
                    await self.load_extension(f"src.cogs.{extension}")
                    self.logger.info(f"Loaded extension {extension}", send_to_log_channel=False)
                except Exception as e:
                    exception = f"{type(e).__name__}: {e}"
                    self.logger.error(f"Failed to load extension {extension}\n{exception}", send_to_log_channel=False)

    # Execute when bot is ready
    async def on_ready(self):
        self.logger.info(f"Logged in as {self.user.name} ({self.user.id})", send_to_log_channel=False)
        self.logger.info(f"Default prefix: {self.prefix}", send_to_log_channel=False)
        self.logger.info(f"Running on servers:  "+", ".join([f"{guild.name} (ID: {guild.id})" for guild in self.guilds]), send_to_log_channel=False)
        # Setup log channel
        self.logger.set_log_channel(self, self.log_channel_id)
        self.logger.info("Bot is ready.")
        await self.tree.sync()
        
    # Execute when bot is closed
    async def close(self):
        self.logger.info("Bot execution terminated.", send_to_log_channel=False)
        await super().close()

    # Bot execution
    def run(self):
        if os.environ.get('TOKEN') is not None:
            token = os.environ.get('TOKEN')
            self.logger.info("Starting bot execution.")
            super().run(token, reconnect=True)
        else:
            self.logger.error("Token not found. Please set the TOKEN environment variable.")
            return
        
    async def on_command(self, context):
        info = f"Command {context.command.name} used by @{context.author.name}"
        info += f" in #{context.channel.name} of {context.guild.name}" if context.guild is not None else f" in DMs."
        self.logger.info(info)
    
    # Bot command error handling
    async def on_command_error(self, context, error):
        err = f"{error} - Occurred while executing '{context.message.content}' by @{context.author.name}"
        err += f" in #{context.channel.name} of {context.guild.name}" if context.guild is not None else f" in DMs."
        self.logger.error(err)
        
        if isinstance(error, commands.CommandNotFound):
            embed = discord.Embed(
                title="Command not found :confused:",
                description=f"Use `{self.prefix}help` to see all available commands.",
                color=0xBEBEFE,
            )   
        elif isinstance(error, commands.MissingRole):
            embed = discord.Embed(
                title="Missing role :confused:",
                description=f"You do not have the required role to use this command.",
                color=0xBEBEFE,
            )
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Missing argument :confused:",
                description=f"Use `{self.prefix}help {context.command.name}` to see the usage.",
                color=0xBEBEFE,
            )
        else:
            embed = discord.Embed(
                title="An error occurred :confused:",
                description=f"An unexpected error occurred while executing the command.",
                color=0xBEBEFE,
            )
        await context.send(embed=embed)
