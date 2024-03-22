#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Log class for all bots '''

#-------------------------------------------------------------------------------

import os
import discord
import asyncio
import logging
from datetime import datetime

base_log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs')

class Logger():
    ''' Logging class definition '''

    def __init__(self, bot_name: str):
        ''' Initialize the log '''
        self.bot_name = bot_name.lower()
        self.log_channel = dict()
        self.log_dir = os.path.join(base_log_dir, self.bot_name)
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, f'{self.bot_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.log')
        logging.basicConfig(filename= self.log_file,
                            level= logging.INFO,
                            format= "%(asctime)s [%(levelname)s] %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S")
        self.log = logging.getLogger(__name__)

    def set_log_channel(self, guild_id: int, log_channel: discord.TextChannel):
        ''' Set the log channel '''
        self.log_channel[guild_id] = log_channel

    def info(self, log_message: str, guild: discord.Guild=None, send_log=True):
        '''Logs an info message'''
        self.log.info(log_message)
        if send_log and guild is not None:
            self.send_log_message(guild, log_message, "info")
    
    def debug(self, log_message: str, guild: discord.Guild=None, send_log=True):
        '''Logs a debug message'''
        self.log.debug(log_message)
        if send_log and guild is not None:
            self.send_log_message(guild, log_message, "debug")
    
    def warning(self, log_message: str, guild: discord.Guild=None, send_log=True):
        '''Logs a warning message'''
        self.log.warning(log_message)
        if send_log and guild is not None:
            self.send_log_message(guild, log_message, "warning")

    def error(self, log_message: str, guild: discord.Guild=None, send_log=True):
        '''Logs an error message'''
        self.log.error(log_message)
        if send_log and guild is not None:
            self.send_log_message(guild, log_message, "error")
    
    def send_log_message(self, log_message: str, guild: discord.Guild=None, level: str="info"):
        '''Sends a message to the log channel'''
        log_channel = self.log_channel.get(guild.id, None)
        if log_channel is not None:
            embed = discord.Embed()
            if level == "info": 
                embed.description = f':information_source: \t `{log_message}`'
                embed.color = discord.Color.dark_grey()
            elif level == "debug":
                embed.description = f':mag: \t `{log_message}` \n{log_channel.guild.owner.mention}'
                embed.color = discord.Color.orange()
            elif level == "error": 
                embed.description = f':interrobang: \t `{log_message}` \n{log_channel.guild.owner.mention}'
                embed.color = discord.Color.red()
            elif level == "warning": 
                embed.title = ""
                embed.description = f':warning: \t `{log_message}` \n{log_channel.guild.owner.mention}'
                embed.color = discord.Color.yellow()
            asyncio.ensure_future(log_channel.send(embed=embed))