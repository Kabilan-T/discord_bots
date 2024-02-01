#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Logging class definition'''

#-------------------------------------------------------------------------------

import os
import discord
import asyncio
import logging
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