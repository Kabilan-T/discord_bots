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

config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yml')
data = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

class BaseBot(commands.Bot):
    ''' Base class for all bots '''

    def __init__(self, bot_name: str, default_color: discord.Color, extensions_to_load: list):
        ''' Initialize the bot '''
        self.load_config(bot_name)
        self.prefix = dict()
        self.default_color = default_color
        self.extensions_to_load = extensions_to_load
        self.log = Logger(self.name)
        self.log.info(f"Loaded config for {self.name}")
        self.data_dir = os.path.join(data, self.name)
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        # Create discord bot
        super().__init__(description="Discord bot : "+self.name,
                         command_prefix=self.get_prefix,
                         intents=discord.Intents.all(),
                         help_command=None,
                         application_id=self.client_id)
        
    def load_config(self, bot_name: str):
        '''Load the configuration file'''
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file).get(bot_name, None)
        if config is None:
            raise ValueError(f"Configuration not found for {bot_name}")
        self.name = config.get('name', None)
        self.user_name = config.get('user_name', None)
        self.client_id = config.get('client_id', None)
        self.default_prefix = config.get('default_prefix', None)

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
    
    async def get_prefix(self, message):
        '''Get the prefix for the bot'''
        if message.guild is None:
            return self.default_prefix
        return self.prefix.get(message.guild.id, self.default_prefix)

    async def on_ready(self):
        ''' Called when the bot is ready '''
        self.log.info(f"Logged in as {self.user.name} ({self.user.id})")    
        for guild in self.guilds:
            self.prefix[guild.id] = self.default_prefix    
            if not os.path.exists(os.path.join(self.data_dir, str(guild.id))):
                os.makedirs(os.path.join(self.data_dir, str(guild.id)))
                self.log.info(f"Data directory created for {guild.name}")
            else:
                self.log.info(f"Data directory for {guild.name} already exists")
                if os.path.exists(os.path.join(self.data_dir, str(guild.id), 'custom_settings.yml')):
                    with open(os.path.join(self.data_dir, str(guild.id), 'custom_settings.yml'), 'r') as file:
                        guild_settings = yaml.safe_load(file)
                    self.log.info(f"Loaded custom settings for {guild.name}")
                    self.prefix[guild.id] = guild_settings.get('prefix', self.default_prefix) 
                    if guild_settings.get('log_channel', None) is not None:
                        self.log.set_log_channel(guild.id, self.get_channel(guild_settings.get('log_channel', None)))
                else:
                    self.log.info(f"No custom settings found for {guild.name}")
            self.log.info(f"{self.name} is ready in {guild.name}; prefix: {self.prefix[guild.id]}", guild)
        await self.tree.sync()
                          
    async def close(self):
        '''Execute when bot is closed'''
        self.log.info("Bot execution terminated.", None, False)
        await super().close()
    
    def run(self, token=None):
        '''Starts the bot execution'''
        if token is not None:
            self.log.info(f"Starting {self.name} bot execution")
            super().run(token, reconnect=True)
        else:
            self.log.error(f"Token not found for {self.name}. Please set the TOKEN as environment variable.")

    async def on_command(self, context: Context):
        ''' Called when a command is used '''
        info = f"Command {context.command.name} used by @{context.author.name}"
        info += f" in #{context.channel.name} of {context.guild.name}" if context.guild is not None else f" in DMs."
        self.log.info(info, context.guild)

    async def on_command_error(self, context : Context, error : Exception):
        '''Execute when a command error occurs'''
        err = f"{error} - Occurred while executing '{context.message.content}' by @{context.author.name}"
        err += f" in #{context.channel.name} of {context.guild.name}" if context.guild is not None else f" in DMs."
        self.log.error(err, context.guild)
        if isinstance(error, commands.CommandNotFound):
            embed = discord.Embed(
                title="Command not found :confused:",
                description=f"Use `{self.prefix[context.guild.id]}help` to see all available commands.",
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
                description=f"Use `{self.prefix[context.guild.id]}help {context.command.name}` to see the usage.",
                color=self.default_color,
            )
        else:
            embed = discord.Embed(
                title="An error occurred :confused:",
                description=f"An unexpected error occurred while executing the command.",
                color=discord.Color.red(),
            )
        await context.send(embed=embed)

    async def on_connect(self):
        ''' Called when the bot connects '''
        self.log.info(f'{self.name} has connected')
    
    async def on_disconnect(self):
        ''' Called when the bot disconnects '''
        self.log.warning(f'{self.name} has disconnected')

    async def on_resumed(self):
        ''' Called when the bot resumes '''
        self.log.info(f'{self.name} has resumed')

   


