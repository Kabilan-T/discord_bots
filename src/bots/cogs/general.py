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
import typing
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
    async def echo(self, context: Context, channel: typing.Optional[discord.TextChannel], *, message: str,):
        '''Repeat the message'''
        if isinstance(channel, str):
            message = channel+" "+message
            channel = None
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
        await channel.send(message)
    
    @commands.command( name="dm", description="Send a direct message to a user.")
    async def dm(self, context: Context, user: typing.Optional[typing.Union[discord.Member, int]], *, message: str):
        if not context.author.guild_permissions.administrator:
            embed = discord.Embed(
                title="Error",
                description="You do not have permission to use this command.",
                color=self.bot.default_color,
                )
            await context.reply(embed=embed)
            return
        if isinstance(user, int):
            user = self.bot.get_user(user)
        try:
            embed = discord.Embed(
                description=message,
                color=self.bot.default_color,
                )
            await user.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(
                title="Error",
                description="The user has disabled direct messages.",
                color=self.bot.default_color,
                )
            await context.reply(embed=embed)
            return 
        embed = discord.Embed(
            title="DM Sent",
            description=f"The message has been sent to {user.name}.",
            color=self.bot.default_color,
            )
        await context.reply(embed=embed)
    
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

    @commands.command( name="load_cog", description="Load a specific cog.")
    @commands.has_permissions(administrator=True)
    async def load_cog(self, context: Context, cog_name: str):
        '''Load a specific cog'''
        if not cog_name.startswith("cogs."):
            cog_name = f'cogs.{self.bot.name.lower().replace("-", "")}.{cog_name}'
        cog_name = f"bots.{cog_name}"
        if cog_name in self.bot.extensions:
            embed = discord.Embed(
                title="Error",
                description=f"`{cog_name}` is already loaded.",
                color=discord.Color.red(),
                )
            await context.send(embed=embed)
            return
        try:
            await self.bot.load_specific_extension(cog_name)
            self.bot.log.info(f"Loaded extension {cog_name}")
            embed = discord.Embed(
                title="Cog Loaded",
                description=f"`{cog_name}` has been loaded.",
                color=self.bot.default_color,
                )
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"Failed to load `{cog_name}`: {e}",
                color=discord.Color.red(),
                )
        await context.send(embed=embed)

    @commands.command( name="unload_cog", description="Unload a specific cog.")
    @commands.has_permissions(administrator=True)
    async def unload_cog(self, context: Context, cog_name: str):
        '''Unload a specific cog'''
        if not cog_name.startswith("cogs."):
            cog_name = f'cogs.{self.bot.name.lower().replace("-", "")}.{cog_name}'
        cog_name = f"bots.{cog_name}"
        if cog_name not in self.bot.extensions:
            embed = discord.Embed(
                title="Error",
                description=f"`{cog_name}` is not loaded.",
                color=discord.Color.red(),
                )
            await context.send(embed=embed)
            return
        try:
            await self.bot.unload_specific_extension(cog_name)
            self.bot.log.info(f"Unloaded extension {cog_name}")
            embed = discord.Embed(
                title="Cog Unloaded",
                description=f"`{cog_name}` has been unloaded.",
                color=self.bot.default_color,
                )
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"Failed to unload `{cog_name}`: {e}",
                color=discord.Color.red(),
                )
        await context.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        '''Convert message from other bots to commands (if begins with prefix)'''
        # ignore messages from the dm channel
        if isinstance(message.channel, discord.DMChannel):
            return
        if message.author.bot and message.content.startswith(self.bot.prefix.get(message.guild.id, self.bot.default_prefix)):
            context = await self.bot.get_context(message)
            if context.valid:
                await self.bot.invoke(context)
            else:
                await self.bot.process_commands(message)


async def setup(bot):
    await bot.add_cog(General(bot))     