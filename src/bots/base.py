#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Base class for all bots '''

#-------------------------------------------------------------------------------

import os
import yaml
import shutil
import discord
from discord.ext import commands
from discord.ext.commands import Context
from bots.log import Logger

config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yml')
data = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

class BaseBot(commands.Bot):
    ''' Base class for all bots '''

    def __init__(self, bot_name: str):
        ''' Initialize the bot '''
        self.bot_name = bot_name
        self.load_config()
        self.prefix = dict()
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
        
    def load_config(self):
        '''Load the configuration file'''
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file).get(self.bot_name, None)
        if config is None:
            raise ValueError(f"Configuration not found for {self.bot_name}")
        self.name = config.get('name', None)
        self.user_name = config.get('user_name', None)
        self.client_id = config.get('client_id', None)
        self.default_prefix = config.get('default_prefix', None)
        self.default_color = config.get('default_color', discord.Color.dark_theme())
        self.extensions_to_load = config.get('extensions', list())

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
    
    async def reload_extensions(self):
        '''Reload the bot cogs'''
        self.load_config()
        self.log.info(f"Reloading extensions for {self.name}")
        self.succeeded = list()
        self.failed = list()
        self.unloaded = list()
        for extension_to_load in self.extensions_to_load:
            try:
                extension = "bots."+extension_to_load
                if extension in self.extensions:
                    await self.reload_extension(extension)
                    self.log.info(f"Reloaded extension {extension}")
                else:
                    await self.load_extension(extension)
                    self.log.info(f"Loaded extension {extension}")
                self.succeeded.append(extension)
            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                self.log.error(f"Failed to reload extension {extension}\n{exception}")
                self.failed.append(extension)
        available_extensions = [extension for extension in self.extensions if extension.startswith('bots.')]
        for extension in available_extensions:
            if extension.replace('bots.', '') not in self.extensions_to_load:
                await self.unload_extension(extension)
                self.unloaded.append(extension)
                self.log.info(f"Unloaded extension {extension}")
        return (self.succeeded, self.failed, self.unloaded)
    
    async def unload_specific_extension(self, extension: str):
        '''Unload a specific extension'''
        if extension in self.extensions:
            await self.unload_extension(extension)
            self.log.info(f"Unloaded extension {extension}")
        else:
            self.log.warning(f"Extension {extension} not found")
        return extension
    
    async def load_specific_extension(self, extension: str):
        '''Load a specific extension'''
        try:
            await self.load_extension(extension)
            self.log.info(f"Loaded extension {extension}")
        except Exception as e:
            exception = f"{type(e).__name__}: {e}"
            self.log.error(f"Failed to load extension {extension}\n{exception}")
        return extension
    
    async def get_prefix(self, message):
        '''Get the prefix for the bot'''
        if message.guild is None:
            return self.default_prefix
        return self.prefix.get(message.guild.id, self.default_prefix)

    def guild_dir(self, guild_id) -> str:
        '''Get the data directory for a guild'''
        return os.path.join(self.data_dir, "guilds", str(guild_id))

    def guild_path(self, guild_id, *parts) -> str:
        '''Get a path inside a guild's data directory'''
        return os.path.join(self.guild_dir(guild_id), *parts)

    def ensure_guild_dir(self, guild_id) -> str:
        '''Create the guild's data directory if it doesn't exist'''
        guild_dir = self.guild_dir(guild_id)
        if not os.path.exists(guild_dir):
            os.makedirs(guild_dir)
        return guild_dir

    def bot_data_path(self, *parts) -> str:
        '''Get a path inside the bot-level (non-guild-specific) data directory'''
        bot_dir = os.path.join(self.data_dir, "bot")
        if not os.path.exists(bot_dir):
            os.makedirs(bot_dir)
        return os.path.join(bot_dir, *parts)

    def list_guild_ids(self) -> list:
        '''List all guild IDs that have a data directory'''
        guilds_dir = os.path.join(self.data_dir, "guilds")
        if not os.path.exists(guilds_dir):
            return []
        return [int(guild_id) for guild_id in os.listdir(guilds_dir)
                if guild_id.isdigit() and os.path.isdir(os.path.join(guilds_dir, guild_id))]

    def load_guild_yaml(self, guild_id, filename, default=None):
        '''Load a YAML file from a guild's data directory'''
        if default is None:
            default = dict()
        file_path = self.guild_path(guild_id, filename)
        if not os.path.exists(file_path):
            return default
        with open(file_path, 'r') as file:
            return yaml.safe_load(file) or default

    def save_guild_yaml(self, guild_id, filename, data):
        '''Save a YAML file to a guild's data directory'''
        self.ensure_guild_dir(guild_id)
        with open(self.guild_path(guild_id, filename), 'w+') as file:
            yaml.dump(data, file)

    def update_guild_yaml(self, guild_id, filename, update_fn, default=None):
        '''Load, mutate and save a guild's YAML file in one step'''
        data = update_fn(self.load_guild_yaml(guild_id, filename, default))
        self.save_guild_yaml(guild_id, filename, data)
        return data

    def delete_guild_file(self, guild_id, filename):
        '''Delete a file from a guild's data directory'''
        file_path = self.guild_path(guild_id, filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    def clear_guild_data(self, guild_id):
        '''Clear all data for a guild'''
        guild_dir = self.guild_dir(guild_id)
        if os.path.exists(guild_dir):
            shutil.rmtree(guild_dir)
        self.ensure_guild_dir(guild_id)

    def load_bot_yaml(self, filename, default=None):
        '''Load a YAML file from the bot-level data directory'''
        if default is None:
            default = dict()
        file_path = self.bot_data_path(filename)
        if not os.path.exists(file_path):
            return default
        with open(file_path, 'r') as file:
            return yaml.safe_load(file) or default

    def save_bot_yaml(self, filename, data):
        '''Save a YAML file to the bot-level data directory'''
        with open(self.bot_data_path(filename), 'w+') as file:
            yaml.dump(data, file)

    async def on_ready(self):
        ''' Called when the bot is ready '''
        self.log.info(f"Logged in as {self.user.name} ({self.user.id})")
        for guild in self.guilds:
            self.prefix[guild.id] = self.default_prefix
            is_new = not os.path.exists(self.guild_dir(guild.id))
            self.ensure_guild_dir(guild.id)
            if is_new:
                self.log.info(f"Data directory created for {guild.name}")
            else:
                self.log.info(f"Data directory for {guild.name} already exists")
                settings = self.load_guild_yaml(guild.id, 'settings.yml')
                if settings:
                    self.log.info(f"Loaded custom settings for {guild.name}")
                    self.prefix[guild.id] = settings.get('prefix', self.default_prefix)
                    if settings.get('log_channel', None) is not None:
                        self.log.set_log_channel(guild.id, self.get_channel(settings.get('log_channel', None)))
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

    async def on_command_error(self, context : Context, e : Exception):
        '''Execute when a command error occurs'''
        if isinstance(e, commands.CommandNotFound):
            embed = discord.Embed(
                title="Command not found :confused:",
                description=f"Use `{self.prefix[context.guild.id]}help` to see all available commands.",
                color=self.default_color,
            )
            self.log.warning(f"Incorrect command used by @{context.author.name} in #{context.channel.name} of {context.guild.name}\nException: `{e}`", context.guild)
            await context.send(embed=embed)
        elif isinstance(e, commands.MissingRole):
            embed = discord.Embed(
                title="Missing role :confused:",
                description=f"You do not have the required role to use this command.",
                color=self.default_color,
            )
            self.log.warning(f"Missing role for command '{context.command.name}' by @{context.author.name} in #{context.channel.name} of {context.guild.name}\nException: `{e}`", context.guild)
            await context.send(embed=embed)
        elif isinstance(e, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Missing argument :confused:",
                description=f"Use `{self.prefix[context.guild.id]}help {context.command.name}` to see the usage.",
                color=self.default_color,
            )
            self.log.warning(f"Missing argument for command '{context.command.name}' by @{context.author.name} in #{context.channel.name} of {context.guild.name}\nException:`{e}`", context.guild)
            await context.send(embed=embed)
        else:
            embed = discord.Embed(
                title="An error occurred :confused:",
                description=f"An unexpected error occurred while executing the command.",
                color=discord.Color.red(),
            )
            if isinstance(context.channel, discord.channel.DMChannel):
                self.log.error(f"Unknown error in command '{context.command.name}' by @{context.author.name} in DMs\nException: `{e}`", context.guild)
            else:
                self.log.error(f"Unknown error in command '{context.command.name}' by @{context.author.name} in #{context.channel.name} of {context.guild.name}\nException: `{e}`", context.guild)
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

   


