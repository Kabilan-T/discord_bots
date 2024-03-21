#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Base class for all bots '''

#-------------------------------------------------------------------------------

import os
import yaml
import discord
from discord.ext import commands
from discord.ext.commands import Context
from bots.log import Logger

config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config')

class BaseBot(commands.Bot):
    ''' Base class for all bots '''

    def __init__(self, config_file: str, default_color: discord.Color, extensions_to_load: list):
        ''' Initialize the bot '''
        self.load_config(config_file)
        self.default_color = default_color
        self.extensions_to_load = extensions_to_load
        self.log = Logger(self.bot_name)
        self.log.info(f"Loaded config for {self.bot_name}")
        # Create discord bot
        super().__init__(description="Discord bot : "+self.bot_name,
                         command_prefix=self.prefix, 
                         intents=discord.Intents.all(),
                         help_command=None,
                         application_id=self.client_id)
        
    def load_config(self, config_file: str):
        '''Load the configuration file'''
        file_path = os.path.join(config_dir, config_file)
        with open(file_path, 'r') as file:
            self.config = yaml.safe_load(file)
        self.bot_name = self.config.get('name', None)
        self.user_name = self.config.get('user_name', None)
        self.client_id = self.config.get('client_id', None)
        self.prefix = self.config.get('prefix', '!')
        self.log_channel_id = self.config.get('log_channel_id', None)

    async def setup_hook(self):
        '''Setup hook executed before bot execution'''
        # Load cogs
        for extension in self.extensions_to_load:
            try:
                await self.load_extension(f"bots.{extension}")
                self.log.info(f"Loaded extension {extension}")
            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                self.log.error(f"Failed to load extension {extension}\n{exception}")

    async def on_ready(self):
        ''' Called when the bot is ready '''
        self.log.info(f"Logged in as {self.user.name} ({self.user.id})")
        self.log.set_log_channel(self.get_channel(self.log_channel_id))
        self.log.info(f'{self.bot_name} is ready')
    
    async def close(self):
        '''Execute when bot is closed'''
        self.log.info("Bot execution terminated.")
        await super().close()
    
    def run(self, token=None):
        '''Starts the bot execution'''
        if token is not None:
            self.log.info(f"Starting {self.bot_name} bot execution")
            super().run(token, reconnect=True)
        else:
            self.log.error(f"Token not found for {self.bot_name}. Please set the TOKEN as environment variable.")

    async def on_command_completion(self, context: Context):
        ''' Called when a command is completed '''
        self.log.info(f'{context.author} has executed {context.command}')

    async def on_command_error(self, context : Context, error : Exception):
        '''Execute when a command error occurs'''
        err = f"{error} - Occurred while executing '{context.message.content}' by @{context.author.name}"
        err += f" in #{context.channel.name} of {context.guild.name}" if context.guild is not None else f" in DMs."
        self.logger.error(err)
        if isinstance(error, commands.CommandNotFound):
            embed = discord.Embed(
                title="Command not found :confused:",
                description=f"Use `{self.prefix}help` to see all available commands.",
                color=self.default_color,
            )   
        elif isinstance(error, commands.MissingRole):
            embed = discord.Embed(
                title="Missing role :confused:",
                description=f"You do not have the required role to use this command.",
                color=self.default_color,
            )
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Missing argument :confused:",
                description=f"Use `{self.prefix}help {context.command.name}` to see the usage.",
                color=self.default_color,
            )
        else:
            embed = discord.Embed(
                title="An error occurred :confused:",
                description=f"An unexpected error occurred while executing the command.",
                color=discord.Color.red(),
            )
        await context.send(embed=embed)

    async def on_error(self, event_method, *args, **kwargs):
        ''' Called when an error occurs '''
        self.log.error(f'Error in {event_method}: {args[0]}')

    async def on_connect(self):
        ''' Called when the bot connects '''
        self.log.info(f'{self.bot_name} has connected')
    
    async def on_disconnect(self):
        ''' Called when the bot disconnects '''
        self.log.warning(f'{self.bot_name} has disconnected')

    async def on_resumed(self):
        ''' Called when the bot resumes '''
        self.log.info(f'{self.bot_name} has resumed')

   


