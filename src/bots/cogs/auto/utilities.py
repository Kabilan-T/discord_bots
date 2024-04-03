#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Utility commands for the bot'''

#-------------------------------------------------------------------------------

import os
import asyncio
import yaml
import discord
import typing
from discord.ext import commands
from discord.ext.commands import Context


# Default permissions : Change 
PermissionToMove = discord.Permissions(move_members=True)
PermissionToPurge = discord.Permissions(manage_messages=True)
PermissionBasic = discord.Permissions(send_messages=True)

class Utility(commands.Cog, name="Utilities"):
    def __init__(self, bot):
        self.bot = bot

    def check(self, context: Context, permission):
        # Check if the user has the required permissions
        has_permissions = context.channel.permissions_for(context.author).is_superset(permission) or context.author.guild_permissions.is_superset(permission)
        if not has_permissions:
            embed = discord.Embed(
                title="Sorry :confused:",
                description="You do not have permission to use this command. You need the following permission to use this command : " + str(permission),
                color=self.bot.default_color,
            )
            context.send(embed=embed)
            self.bot.log.warning(f"{context.author.name} tried to use a command. But they do not have the required permissions - {permission}", context.guild)
        return has_permissions

    @commands.command( name="nick", description="Change the nickname of a member.")
    async def nick(self, context: Context, member: discord.Member, nickname: str = None):
        '''Change the nickname of a member, if nickname is None, the nickname is removed'''
        if self.check(context, PermissionToPurge):
            await member.edit(nick=nickname)
            if nickname is None:
                self.bot.log.info(f"{context.author.name} removed the nickname of {member.name} in {context.guild.name}", context.guild)
                embed = discord.Embed(
                    title="Nickname :name_badge:",
                    description=f"The nickname of {member.mention} has been removed.",
                    color=self.bot.default_color,
                )
                await context.send(embed=embed)
            else:
                self.bot.log.info(f"{context.author.name} changed the nickname of {member.name} to {nickname} in {context.guild.name}", context.guild)
                embed = discord.Embed(
                    title="Nickname :name_badge:",
                    description=f"The nickname of {member.mention} has been changed to {nickname}.",
                    color=self.bot.default_color,
                )
                await context.send(embed=embed)
    
    @commands.command( name="purge", description="Purge messages from a channel.")
    async def purge(self, context: Context, amount: int):
        '''Purge messages from a channel'''
        if self.check(context, PermissionToPurge):
            self.bot.log.info(f"{context.author.name} purged {amount} messages from {context.channel.name} in {context.guild.name}", context.guild)
            await context.channel.purge(limit=amount)
            embed = discord.Embed(
                title="Purge :wastebasket:",
                description=f"{amount} messages have been purged from {context.channel.mention}",
                color=self.bot.default_color,
            )
            await context.send(embed=embed)
    
    @commands.command( name="purge_user", description="Purge messages from a user in one or all channels.")
    async def purgeuser(self, context: Context, member: discord.Member, amount: int, channel: typing.Optional[discord.TextChannel] = None):
        '''Purge messages from a user in one or all channels'''
        if self.check(context, PermissionToPurge):
            if channel is None:
                self.bot.log.info(f"{context.author.name} purged {amount} messages from {member.name} in all channels in {context.guild.name}", context.guild)
                for channel in context.guild.text_channels:
                    await channel.purge(limit=amount, check=lambda message: message.author == member)
                embed = discord.Embed(
                    title="Purge :wastebasket:",
                    description=f"{amount} messages from {member.mention} have been purged from all channels.",
                    color=self.bot.default_color,
                )
                await context.send(embed=embed)
            else:
                self.bot.log.info(f"{context.author.name} purged {amount} messages from {member.name} in {channel.name} in {context.guild.name}", context.guild)
                await channel.purge(limit=amount, check=lambda message: message.author == member)
                embed = discord.Embed(
                    title="Purge :wastebasket:",
                    description=f"{amount} messages from {member.mention} have been purged from {channel.mention}",
                    color=self.bot.default_color,
                )
                await context.send(embed=embed)
    
    @commands.command( name="move", description="Move a member to a different voice channel.")
    async def move(self, context: Context, member: discord.Member, channel: discord.VoiceChannel, reason: str = None):
        '''Move a member to a different voice channel'''
        if self.check(context, PermissionToMove):
            self.bot.log.info(f"{context.author.name} moved {member.name} to {channel.name} in {context.guild.name}", context.guild)
            embed = discord.Embed(
                title="Move :arrow_right:",
                description=f"{member.mention} has been moved to {channel.mention}",
                color=self.bot.default_color,
            )
            await context.send(embed=embed)
            await member.move_to(channel, reason=reason)
    
    @commands.command( name="disconnect", description="Disconnect a member from the voice channel.")
    async def disconnect(self, context: Context, member: discord.Member, reason: str = None):
        '''Disconnect a member from the voice channel'''
        if self.check(context, PermissionToMove):
            self.bot.log.info(f"{context.author.name} disconnected {member.name} in {context.guild.name}", context.guild)
            embed = discord.Embed(
                title="Disconnect :x:",
                description=f"{member.mention} has been disconnected from the voice channel.",
                color=self.bot.default_color,
            )
            await context.send(embed=embed)
            await member.move_to(None, reason=reason)
    
    @commands.command( name="sleep", description="Disconnect a member from the voice channel after a certain time.")
    async def sleep(self, context: Context, member: discord.Member, time: int, reason: str = None):
        '''Disconnect a member from the voice channel after a certain time'''
        if self.check(context, PermissionToMove):
            if time < 1:
                embed = discord.Embed(
                    title="Sleep :zzz:",
                    description="The time should be greater than 0.",
                    color=self.bot.default_color,
                )
                await context.send(embed=embed)
                return
            if member.voice is None:
                embed = discord.Embed(
                    title="Sleep :zzz:",
                    description=f"{member.mention} is not in a voice channel.",
                    color=self.bot.default_color,
                )
                await context.send(embed=embed)
                return
            self.bot.log.info(f"{context.author.name} disconnected {member.name} in {context.guild.name} after {time} minutes", context.guild)
            embed = discord.Embed(
                title="Sleep :zzz:",
                description=f"{member.mention} will be disconnected from the voice channel after {time} minutes.",
                color=self.bot.default_color,
            )
            await context.send(embed=embed)
            await asyncio.sleep(time*60)
            embed = discord.Embed(
                title="Sleep :zzz:",
                description=f"{member.mention} has been disconnected from the voice channel after {time} minutes.",
                color=self.bot.default_color,
            )
            await context.send(embed=embed)
            await member.move_to(None, reason=reason)
    
    @commands.command( name="move_all", description="Move all members to a different voice channel.")
    async def moveall(self, context: Context, channel: discord.VoiceChannel, new_channel: discord.VoiceChannel, reason: str = None):
        '''Move all members to a different voice channel'''
        if self.check(context, PermissionToMove):
            self.bot.log.info(f"{context.author.name} moved all members from {channel.name} to {new_channel.name} in {context.guild.name}", context.guild)
            for member in channel.members:
                embed = discord.Embed(
                    title="Move :arrow_right:",
                    description=f"{member.mention} has been moved to {new_channel.mention}",
                    color=self.bot.default_color,
                )
                await context.send(embed=embed)
                await member.move_to(new_channel, reason=reason)
    
    @commands.command( name="disconnect_all", description="Disconnect all members from the voice channel.")
    async def disconnectall(self, context: Context, channel: discord.VoiceChannel, reason: str = None):
        '''Disconnect all members from the voice channel'''
        if self.check(context, PermissionToMove):
            self.bot.log.info(f"{context.author.name} disconnected all members from {channel.name} in {context.guild.name}", context.guild)
            for member in channel.members:
                embed = discord.Embed(
                    title="Disconnect :x:",
                    description=f"{member.mention} has been disconnected from the voice channel.",
                    color=self.bot.default_color,
                )
                await member.move_to(None, reason=reason)

    @commands.command( name="limit_voice", description="Limit the number of members in a voice channel.")
    async def limitvoice(self, context: Context,  channel: typing.Optional[discord.VoiceChannel] = None, limit: typing.Optional[int] = None):
        '''Limit the number of members in a voice channel, if limit is None, the limit is removed'''
        if self.check(context, PermissionToMove):
            if channel is None:
                if context.author.voice is None:
                    embed = discord.Embed(
                        title="Voice Channel Limit :loud_sound:",
                        description="Please specify a voice channel or join a voice channel to set the limit.",
                        color=self.bot.default_color,
                    )
                    await context.send(embed=embed)
                    return
                channel = context.author.voice.channel
            if limit is None or limit <= 0:
                await channel.edit(user_limit=None)
                self.bot.log.info(f"{context.author.name} removed the limit of {channel.name} in {context.guild.name}", context.guild)
                embed = discord.Embed(
                    title="Voice Channel Limit :loud_sound:",
                    description=f"The limit of {channel.mention} has been removed.",
                    color=self.bot.default_color,
                )
                await context.send(embed=embed)
            else:
                await channel.edit(user_limit=limit)
                self.bot.log.info(f"{context.author.name} set the limit of {channel.name} to {limit} in {context.guild.name}", context.guild)
                embed = discord.Embed(
                    title="Voice Channel Limit :loud_sound:",
                    description=f"The limit of {channel.mention} has been set to {limit}.",
                    color=self.bot.default_color,
                )
                await context.send(embed=embed)
    
                 
async def setup(bot):
    await bot.add_cog(Utility(bot))