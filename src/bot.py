#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Discord bot class definition'''

#-------------------------------------------------------------------------------

import os
import yaml
import logging
import discord
from discord.ext import commands
from datetime import datetime

class MyBot(commands.Bot):
    def __init__(self):

        # Setup logging
        self.logger = self.setup_logging()

        # Load discord bot config
        config = yaml.load(open(os.path.join(os.path.dirname(__file__), "config", "bot.yml"), "r"), Loader=yaml.FullLoader)
        self.name = config["name"]
        self.username = config["username"]
        self.prefix = config["default_prefix"]
        self.client_id = config["client_id"]
        self.extensions_to_load = config["extensions"]
        self.logger.info(f"Loaded config for {self.name}")

        # Create discord bot
        super().__init__(description="Discord bot : "+self.name,
                         command_prefix=self.prefix, 
                         intents=discord.Intents.all(),
                         help_command=None,
                         application_id=self.client_id)
        
    def setup_logging(self):
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_file = os.path.join(log_dir, f"bot_{datetime.now().strftime('%Y%m%d%H%M%S')}.log")
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        return logging.getLogger(__name__)


    async def setup_hook(self):
        # Load utils
        for extension in self.extensions_to_load:
            if os.path.isfile(os.path.join(os.path.dirname(__file__), "utils", extension+".py")):
                try:
                    await self.load_extension(f"src.utils.{extension}")
                    self.logger.info(f"Loaded extension {extension}")
                except Exception as e:
                    exception = f"{type(e).__name__}: {e}"
                    self.logger.error(f"Failed to load extension {extension}\n{exception}")

    # Execute when bot is ready
    async def on_ready(self):
        self.logger.info("Bot is ready.")
        info = f"Statup info for {self.name}:\n"
        info += f"Logged in as {self.user.name} ({self.user.id})\n"
        info += f"Default prefix: {self.prefix}\n"
        info += "Running on servers:"
        for guild in self.guilds:
            info += f"\n\t - {guild.name} (ID: {guild.id}) with {guild.member_count} members"
        self.logger.info(info)
        self.logger.info("Time to get to work!")
        await self.tree.sync()
        
    # Execute when bot is closed
    async def close(self):
        await super().close()
        self.logger.info("Bot execution terminated.")

    # Bot execution
    def run(self):
        
        if os.environ.get('TOKEN') is not None:
            token = os.environ.get('TOKEN')
            self.logger.info("Starting bot execution.")
            super().run(token, reconnect=True)
        else:
            self.logger.error("Token not found. Please set the TOKEN environment variable.")
            return
        
    async def on_command(self, ctx):
        info = f"Command {ctx.command.name} used by @{ctx.author.name}"
        info += f" in #{ctx.channel.name} of {ctx.guild.name}" if ctx.guild is not None else f" in DMs."
        self.logger.info(info)
    

    # Bot command error handling
    async def on_command_error(self, ctx, error):
        err = f"{error} - Occurred while executing '{ctx.message.content}' by @{ctx.author.name}"
        err += f" in #{ctx.channel.name} of {ctx.guild.name}" if ctx.guild is not None else f" in DMs."
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
                description=f"Use `{self.prefix}help {ctx.command.name}` to see the usage.",
                color=0xBEBEFE,
            )
        else:
            embed = discord.Embed(
                title="An error occurred :confused:",
                description=f"An unexpected error occurred while executing the command.",
                color=0xBEBEFE,
            )
        await ctx.send(embed=embed)
    
