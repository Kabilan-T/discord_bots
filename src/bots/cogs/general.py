#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' General commands for the bot'''

#-------------------------------------------------------------------------------

import os
import io
import yaml
import zipfile
import discord
from discord.ext import commands
from discord.ext.commands import Context


class General(commands.Cog, name="General"):
    def __init__(self, bot):
        '''Initializes the general cog'''
        self.bot = bot
    
    @commands.command( name="hello", description="Say hello to the bot.", aliases=["hi", "hey"])
    async def hello(self, context: Context):
        '''Say hello to the bot'''
        embed = discord.Embed(
            title="Hello "+context.author.name+" :wave:",
            description=f"I am {self.bot.name}, a discord bot. Nice to meet you! :smile:",
            color=self.bot.default_color,
        )
        await context.send(embed=embed)

    @commands.command( name="ping", description="Check if the bot is alive.", aliases=["p"])
    async def ping(self, context: Context):
        '''Check if the bot is active and send the latency'''
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"The bot latency is {round(self.bot.latency * 1000)}ms.",
            color=self.bot.default_color,
        )
        await context.send(embed=embed)
    
    @commands.command( name="help", description="Get help on a command." , aliases=["h"])
    async def help(self, context: Context, command: str = None):
        '''Get help on a command'''
        if command is None:
            embed = discord.Embed(
                title="Help",
                description=f"Use `{self.bot.prefix[context.guild.id]}help <command>` to get help on a specific command.",
                color=self.bot.default_color,
            )
            for cog in self.bot.cogs:
                cog_commands = self.bot.get_cog(cog).get_commands()
                if len(cog_commands) > 0:
                    embed.add_field(
                        name=cog,
                        value="\n".join([f"***`{command.name}`*** - {command.description}" for command in cog_commands]),
                        inline=False,
                    )
            await context.send(embed=embed)
        else:
            command = self.bot.get_command(command)
            if command is None:
                embed = discord.Embed(
                    title="Help",
                    description=f"`{command}` is not a valid command.",
                    color=self.bot.default_color,
                )
                await context.send(embed=embed)
            else:
                embed = discord.Embed(
                    title=f"Help: {command.name}",
                    description=command.description,
                    color=self.bot.default_color,
                )
                embed.add_field(
                    name="Usage",
                    value=f"`{self.bot.prefix[context.guild.id]}{command.name} {command.signature}`",
                    inline=False,
                )
                await context.send(embed=embed)

    @commands.command( name="prefix", description="Change the bot prefix.")
    @commands.has_permissions(administrator=True)
    async def prefix(self, context: Context, prefix: str = None):
        '''Change or get the bot prefix'''
        if prefix is None:
            embed = discord.Embed(
                title="Prefix",
                description=f"The current prefix is `{self.bot.prefix.get(context.guild.id, self.bot.default_prefix)}`",
                color=self.bot.default_color,
            )
            await context.send(embed=embed)
        else:
            self.bot.prefix[context.guild.id] = prefix
            if os.path.exists(os.path.join(self.bot.data_dir, str(context.guild.id), 'custom_settings.yml')):
                with open(os.path.join(self.bot.data_dir, str(context.guild.id), 'custom_settings.yml'), 'r') as file:
                    guild_settings = yaml.safe_load(file)
                    guild_settings['prefix'] = prefix
            else:
                guild_settings = {'prefix': prefix}
            with open(os.path.join(self.bot.data_dir, str(context.guild.id), 'custom_settings.yml'), 'w+') as file:
                yaml.dump(guild_settings, file)
            embed = discord.Embed(
                title="Prefix",
                description=f"The prefix has been changed to `{self.bot.prefix.get(context.guild.id, self.bot.default_prefix)}`",
                color=self.bot.default_color,
            )
            await context.send(embed=embed)
            self.bot.log.info(f"Prefix changed to {self.bot.prefix.get(context.guild.id, self.bot.default_prefix)}", context.guild)

    @commands.command( name="invite", description="Get the bot invite link.")
    @commands.has_permissions(administrator=True)
    async def invite(self, context: Context):
        '''Send the bot invite link with permissions of admin'''
        embed = discord.Embed(
            title="Invite",
            description=f"Use this link to invite the bot to your server: https://discord.com/oauth2/authorize?client_id={self.bot.client_id}&scope=bot&permissions=8",
            color=self.bot.default_color,
        )
        await context.send(embed=embed)
    
    @commands.command( name="reload", description="Reload the bot cogs.")
    @commands.has_permissions(administrator=True)
    async def reload(self, context: Context):
        '''Reload the bot cogs'''
        (succeeded_reloads, failed_reloads) = await self.bot.reload_extensions()
        embed = discord.Embed(
            title="Cogs Reloaded :gear:",
            color=self.bot.default_color,
        )
        if len(succeeded_reloads) > 0:
            embed.add_field(
                name="Succeeded",
                value=f"\n".join([f":thumbsup: `{cog}`" for cog in succeeded_reloads]),
                inline=False,
            )
        if len(failed_reloads) > 0:
            embed.add_field(
                name="Failed",
                value=f"\n".join([f":thumbsdown: `{cog}`" for cog in failed_reloads]),
                inline=False,
            )
        await context.send(embed=embed)

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


async def setup(bot):
    await bot.add_cog(General(bot))     