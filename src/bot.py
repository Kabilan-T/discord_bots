#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Discord bot class definition'''

#-------------------------------------------------------------------------------

import os
import yaml
import asyncio
import logging
import discord
from discord.ext import commands
from datetime import datetime

class BotLogger():
    def __init__(self):
        self.bot = None
        self.log_channel = None
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"bot_{datetime.now().strftime('%Y%m%d%H%M%S')}.log")
        logging.basicConfig(filename=log_file , 
                            level= logging.INFO,
                            format= "%(asctime)s [%(levelname)s] %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S")
        self.logger = logging.getLogger(__name__)
    
    def set_log_channel(self, bot, channel_id):
        self.bot = bot
        self.log_channel = self.bot.get_channel(int(channel_id))

    def send_message_to_log_channel(self, msg, level):
        if self.log_channel is not None:
            embed = discord.Embed()
            if level == "info": 
                embed.description = f':information_source: \t `{msg}`'
                embed.color = 0xBEBEFE
            elif level == "debug":
                embed.description = f':mag: \t `{msg}` \n{self.log_channel.guild.owner.mention}'
                embed.color = 0x00FF00
            elif level == "error": 
                embed.description = f':interrobang: \t `{msg}` \n{self.log_channel.guild.owner.mention}'
                embed.color = 0xFF0000
            elif level == "warning": 
                embed.title = ""
                embed.description = f':warning: \t `{msg}` \n{self.log_channel.guild.owner.mention}'
                embed.color = 0xFFA500
            asyncio.ensure_future(self.log_channel.send(embed=embed))

    def info(self, msg, send_to_log_channel=True):
        self.logger.info(msg)
        if send_to_log_channel:
            self.send_message_to_log_channel(msg, "info")
    
    def error(self, msg, send_to_log_channel=True):
        self.logger.error(msg)
        if send_to_log_channel:
            self.send_message_to_log_channel(msg, "error")
    
    def warning(self, msg, send_to_log_channel=True):
        self.logger.warning(msg)
        if send_to_log_channel:
            self.send_message_to_log_channel(msg, "warning")
    
    def debug(self, msg, send_to_log_channel=True):
        self.logger.debug(msg)
        if send_to_log_channel:
            self.send_message_to_log_channel(msg, "debug")
    
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
        self.logger.info("Bot execution terminated.")
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
