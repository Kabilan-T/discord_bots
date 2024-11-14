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
    
    @commands.command( name="echo", description="Repeat the message.")
    async def echo(self, context: Context, channel: discord.TextChannel = None, title: str = None, *, message: str = None):
        '''Repeat the message'''
        if channel is None:
            channel = context.channel
        if not channel.permissions_for(context.author).send_messages:
            embed = discord.Embed(
                title="Error",
                description="You do not have permission to send messages in this channel.",
                color=self.bot.error_color,
                )
            await context.reply(embed=embed)
            return
        if title is None:
            title = ""
        if message is None:
            message = title
            title = ""
        embed = discord.Embed(
            title=title,
            description=message,
            color=self.bot.default_color,
            )
        await channel.send(embed=embed)
    
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
                if cog == "Manage" and not context.author.guild_permissions.administrator:
                    continue
                cog_commands = self.bot.get_cog(cog).get_commands()
                if len(cog_commands) > 0:
                    embed.add_field(name=cog,
                                    value="\n".join([f"***`{command.name}`*** {' | '.join([f'**(`{alias}`)**' for alias in command.aliases]) if command.aliases else ''} - {command.description}"for command in cog_commands]),
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
        (succeeded_reloads, failed_reloads, unloaded) = await self.bot.reload_extensions()
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
        if len(unloaded) > 0:
            embed.add_field(
                name="Unloaded",
                value=f"\n".join([f":x: `{cog}`" for cog in unloaded]),
                inline=False,
                )
        await context.send(embed=embed)


async def setup(bot):
    await bot.add_cog(General(bot))     