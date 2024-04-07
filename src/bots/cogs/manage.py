#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Manage cog for the bot'''

#-------------------------------------------------------------------------------

import os
import io
import yaml
import zipfile
import discord
from discord.ext import commands
from discord.ext.commands import Context

class Manage(commands.Cog, name="Manage"):
    def __init__(self, bot):
        '''Initializes the bot management cog'''
        self.bot = bot

    @commands.command( name="set_log_channel", description="Set the log channel for the bot.")
    @commands.has_permissions(administrator=True)
    async def setlogchannel(self, context: Context, channel: discord.TextChannel):
        '''Set the log channel for the bot'''
        self.bot.log.set_log_channel(context.guild.id, channel)
        if os.path.exists(os.path.join(self.bot.data_dir, str(context.guild.id), 'custom_settings.yml')):
            with open(os.path.join(self.bot.data_dir, str(context.guild.id), 'custom_settings.yml'), 'r') as file:
                guild_settings = yaml.safe_load(file)
                guild_settings['log_channel'] = channel.id
        else:
            guild_settings = {'log_channel': channel.id}
        with open(os.path.join(self.bot.data_dir, str(context.guild.id), 'custom_settings.yml'), 'w+') as file:
            yaml.dump(guild_settings, file)
        embed = discord.Embed(
            title="Log Channel",
            description=f"Log channel has been set to {channel.mention}",
            color=self.bot.default_color,
        )
        await context.send(embed=embed)
        self.bot.log.info(f"Log channel set to {channel.mention}", context.guild)

    @commands.command( name="get_logs", description="Send the recent log file.")
    @commands.has_permissions(administrator=True)
    async def getlogs(self, context: Context):
        '''Get the recent log file'''
        file_name = self.bot.log.log_file
        with open(file_name, 'r') as f:
            text = f.read()
        file = discord.File(filename=file_name.split("/")[-1],
                            fp=io.StringIO(text))
        embed = discord.Embed(
            title="Log File :scroll:",
            description="Here is the recent log file. :file_folder:",
            color=self.bot.default_color,
        )
        await context.reply(embed=embed, file=file)
        self.bot.log.info(f"Log file sent to {context.author.name}", context.guild)

    @commands.command( name="get_data", description="Send the data of the bot as zip file.")
    @commands.has_permissions(administrator=True)
    async def getdata(self, context: Context):
        '''Get the data of the bot'''
        if os.path.exists(os.path.join(self.bot.data_dir, str(context.guild.id))):
            dir_path = os.path.join(self.bot.data_dir, str(context.guild.id))
            zip_file_path = os.path.join(self.bot.data_dir, f"{context.guild.id}.zip")
            with zipfile.ZipFile(zip_file_path, 'w') as zipf:
                for root, dirs, files in os.walk(dir_path):
                    for file in files:
                        zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), dir_path))
            file = discord.File(filename=f"{self.bot.name}_{context.guild.id}.zip",  
                                fp=zip_file_path)
            embed = discord.Embed(
                title="Data :file_folder:",
                description="Here is the data of the bot.",
                color=self.bot.default_color,
            )
            await context.reply(embed=embed, file=file)
            self.bot.log.info(f"Data sent to {context.author.name}", context.guild)
            os.remove(zip_file_path)
        else:
            embed = discord.Embed(
                title="Data",
                description="No data found.",
                color=self.bot.default_color,
            )
            await context.send(embed=embed)
    
    @commands.command( name="clear_data", description="Clear the data of the bot including custom settings.")
    @commands.has_permissions(administrator=True)
    async def cleardata(self, context: Context):
        '''Clear the data of the bot'''
        if os.path.exists(os.path.join(self.bot.data_dir, str(context.guild.id))):
            for file in os.listdir(os.path.join(self.bot.data_dir, str(context.guild.id))):
                os.remove(os.path.join(self.bot.data_dir, str(context.guild.id), file))
        self.bot.log.info(f"Data cleared", context.guild)
        self.bot.log.remove_log_channel(context.guild.id)
        embed = discord.Embed(
            title="Data Cleared :wastebasket:",
            description="The data of the bot has been cleared. Cogs will be reloaded to apply changes.",
            color=self.bot.default_color,
        )
        await context.send(embed=embed)
        await self.reload(context)


async def setup(bot):
    await bot.add_cog(Manage(bot))     