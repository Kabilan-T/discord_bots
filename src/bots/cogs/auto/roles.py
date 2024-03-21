#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Role management features such as adding and removing roles '''

#-------------------------------------------------------------------------------

import os
import yaml
import discord
from discord.ext import commands
from discord.ext.commands import Context

class Roles(commands.Cog, name="Roles"):
    def __init__(self, bot):
        '''Initializes the role cog'''
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        ''' Assign roles to a member when they join the server '''
        guild = member.guild
        if guild.id != 1182777669373399202:
    