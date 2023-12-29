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



class MyBot(commands.Bot):
    def __init__(self):

        # Load discord token from config file
        config = yaml.load(open(os.path.join(os.path.dirname(__file__), "config", "bot.yml"), "r"), Loader=yaml.FullLoader)
        self.name = config["name"]
        self.username = config["username"]
        self.prefix = config["default_prefix"]
        self.client_id = config["client_id"]

        # Create discord bot
        intents = discord.Intents.default()
        intents.members = True
        intents.presences = True
        intents.message_content = True
        super().__init__(description="Discord bot : "+self.name,
                         command_prefix=self.prefix, 
                         intents=intents,
                         help_command=None)

    async def setup_hook(self):
        # Load utils
        for filename in os.listdir(os.path.join(os.path.dirname(__file__), "utils")):
            if filename.endswith(".py") and filename != "__init__.py":
                extension = filename[:-3]
                try:
                    await self.load_extension(f"src.utils.{extension}")
                    print(f"Loaded extension {extension}")
                except Exception as e:
                    exception = f"{type(e).__name__}: {e}"
                    print(f"Failed to load extension {extension}\n{exception}")

    # Execute when bot is ready
    async def on_ready(self):
        print(f"Logged in as {self.user.name} ({self.user.id})")
        print(f"Default prefix: {self.prefix}")
        print("Servers:")
        for guild in self.guilds:
            print(f"\t - {guild.name} (ID: {guild.id})")
            print(f"\t\t - Owner: {guild.owner}")
            print(f"\t\t - Created at: {guild.created_at}")
            print(f"\t\t - Members: {guild.member_count}")

        print("------")
        
    # Execute when bot is closed
    async def close(self):
        await super().close()
        print("Bot is shutting down.")

    # Bot execution
    def run(self):
    
        token =  os.getenv('TOKEN') #config["token"]
        super().run(token, reconnect=True)
    

    # Bot command error handling
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("Command not found. Use `$$help` for a list of available commands.")
        elif isinstance(error, commands.MissingRole):
            await ctx.send("You do not have the required role to use this command.")
        else:
            print(f"An error occurred: {error}")
            await ctx.send("An error occurred while executing the command.")
