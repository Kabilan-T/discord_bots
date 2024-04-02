#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Moderation commands for the bot'''

#-------------------------------------------------------------------------------

import os
import asyncio
import yaml
import discord
from discord.ext import commands
from discord.ext.commands import Context


# Default permissions : Change 
PermissionToBan = discord.Permissions(ban_members=True)
PermissionToWarn = discord.Permissions(moderate_members=True)
PermissionToKick = discord.Permissions(kick_members=True)
PermissionToMute = discord.Permissions(mute_members=True)
PermissionToDeafen = discord.Permissions(deafen_members=True)
PermissionToMove = discord.Permissions(move_members=True)
PermissionToPurge = discord.Permissions(manage_messages=True)
PermissionBasic = discord.Permissions(send_messages=True)

class Moderation(commands.Cog, name="Moderation"):
    def __init__(self, bot):
        self.bot = bot
        self.warns = dict()
        self.read_warns()

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
    
    async def send_message(self, context: Context, member: discord.Member, action: str, reason: str = None, dm : bool = False):
        embed = discord.Embed(
            title="Moderation activity :judge:",
            description=f"**{member.mention}** has been {action} by **{context.author.mention}**.",
            color=self.bot.default_color,
        )
        if reason is not None:
            embed.add_field(name="Reason", value=reason, inline=False)
        await context.send(embed=embed)
        if dm:
            await self.send_dm(context, member, action, reason)

    async def send_dm(self, context: Context, member: discord.Member, action: str, reason: str = None):
        embed = discord.Embed(
            title="Moderation activity :judge:",
            description=f"You have been {action} in **{context.guild.name}**",
            color=self.bot.default_color,
        )
        if reason is not None:
            embed.add_field(name="Reason", value=reason, inline=False)
        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            self.bot.log.warning(f"Could not send DM to @{member.name} about {action} activity in {context.guild.name}", context.guild)
            pass
        
    @commands.hybrid_command( name="ban", description="Ban a member from the server.")
    async def ban(self, context: Context, member: discord.Member, reason: str = None):
        '''Ban a member from the server'''
        if self.check(context, PermissionToBan):
            self.bot.log.info(f"{context.author.name} banned {member.name} from {context.guild.name}", context.guild)
            await self.send_message(context, member, "banned :no_entry:", reason, False)
            await member.ban(reason=reason)
    
    @commands.hybrid_command( name="unban", description="Unban a member from the server.")
    async def unban(self, context: Context, member: discord.Member, reason: str = None):
        '''Unban a member from the server'''
        if self.check(context, PermissionToBan):
            self.bot.log.info(f"{context.author.name} unbanned {member.name} in {context.guild.name}", context.guild)
            await self.send_message(context, member, "unbanned :unlock:", reason, False)
            await member.unban(reason=reason)

    @commands.hybrid_command( name="kick", description="Kick a member from the server.")
    async def kick(self, context: Context, member: discord.Member, reason: str = None):
        '''Kick a member from the server'''
        if self.check(context, PermissionToKick):
            self.bot.log.info(f"{context.author.name} kicked {member.name} from {context.guild.name}", context.guild)
            await self.send_message(context, member, "kicked :boxing_glove:", reason, False)
            await member.kick(reason=reason)
    
    @commands.hybrid_command( name="mute", description="Mute a member in the server.")
    async def mute(self, context: Context, member: discord.Member, reason: str = None):
        '''Mute a member in the server'''
        if self.check(context, PermissionToMute):
            self.bot.log.info(f"{context.author.name} muted {member.name} in {context.guild.name}", context.guild)
            await self.send_message(context, member, "muted :shushing_face:", reason, False)
            await member.edit(mute=True, reason=reason)

    @commands.hybrid_command( name="unmute", description="Unmute a member in the server.")
    async def unmute(self, context: Context, member: discord.Member, reason: str = None):
        '''Unmute a member in the server'''
        if self.check(context, PermissionToMute):
            self.bot.log.info(f"{context.author.name} unmuted {member.name} in {context.guild.name}", context.guild)
            await self.send_message(context, member, "unmuted :microphone2:", reason, False)
            await member.edit(mute=False, reason=reason)
    
    @commands.hybrid_command( name="deafen", description="Deafen a member in the server.")
    async def deafen(self, context: Context, member: discord.Member, reason: str = None):
        '''Deafen a member in the server'''
        if self.check(context, PermissionToDeafen):
            self.bot.log.info(f"{context.author.name} deafened {member.name} in {context.guild.name}", context.guild)
            await self.send_message(context, member, "deafened :mute:", reason, False)
            await member.edit(deafen=True, reason=reason)
    
    @commands.hybrid_command( name="undeafen", description="Undeafen a member in the server.")
    async def undeafen(self, context: Context, member: discord.Member, reason: str = None):
        '''Undeafen a member in the server'''
        if self.check(context, PermissionToDeafen):
            self.bot.log.info(f"{context.author.name} undeafened {member.name} in {context.guild.name})", context.guild)
            await self.send_message(context, member, "undeafened :loud_sound:", reason, False)
            await member.edit(deafen=False, reason=reason)
    
    @commands.hybrid_command( name="move", description="Move a member to a different voice channel.")
    async def move(self, context: Context, member: discord.Member, channel: discord.VoiceChannel, reason: str = None):
        '''Move a member to a different voice channel'''
        if self.check(context, PermissionToMove):
            self.bot.log.info(f"{context.author.name} moved {member.name} to {channel.name} in {context.guild.name}", context.guild)
            await self.send_message(context, member, "moved to " + channel.name + " :arrow_right:", reason, False)
            await member.move_to(channel, reason=reason)
    
    @commands.hybrid_command( name="moveall", description="Move all members to a different voice channel.")
    async def moveall(self, context: Context, channel: discord.VoiceChannel, new_channel: discord.VoiceChannel, reason: str = None):
        '''Move all members to a different voice channel'''
        if self.check(context, PermissionToMove):
            self.bot.log.info(f"{context.author.name} moved all members from {channel.name} to {new_channel.name} in {context.guild.name}", context.guild)
            for member in channel.members:
                await self.send_message(context, member, "moved to " + new_channel.name + " :arrow_right:", reason, False)
                await member.move_to(new_channel, reason=reason)

    @commands.hybrid_command( name="disconnect", description="Disconnect a member from the voice channel.")
    async def disconnect(self, context: Context, member: discord.Member, reason: str = None):
        '''Disconnect a member from the voice channel'''
        if self.check(context, PermissionToMove):
            self.bot.log.info(f"{context.author.name} disconnected {member.name} in {context.guild.name}", context.guild)
            await self.send_message(context, member, "disconnected from voice channel :x:", reason, False)
            await member.move_to(None, reason=reason)
    
    @commands.hybrid_command( name="disconnectall", description="Disconnect all members from the voice channel.")
    async def disconnectall(self, context: Context, channel: discord.VoiceChannel, reason: str = None):
        '''Disconnect all members from the voice channel'''
        if self.check(context, PermissionToMove):
            self.bot.log.info(f"{context.author.name} disconnected all members from {channel.name} in {context.guild.name}", context.guild)
            for member in channel.members:
                await self.send_message(context, member, "disconnected from voice channel :x:", reason, False)
                await member.move_to(None, reason=reason)

    @commands.hybrid_command( name="sleep", description="Disconnect a member from the voice channel after a certain time.")
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
            await self.send_message(context, member, "auto disconnected from voice channel after sleep time of " + str(time) + " minutes :zzz: set", reason, True)
            await member.move_to(None, reason=reason)
    
    @commands.hybrid_command( name="limit_voice", description="Limit the number of members in a voice channel.")
    async def limit_voice(self, context: Context, limit: int = None, channel: discord.VoiceChannel = None):
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
    
    @commands.hybrid_command( name="nick", description="Change the nickname of a member.")
    async def nick(self, context: Context, member: discord.Member, nickname: str = None):
        '''Change the nickname of a member, if nickname is None, the nickname is removed'''
        if self.check(context, PermissionToMute):
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
    
    @commands.hybrid_command( name="purge", description="Purge messages from a channel.")
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
    
    @commands.hybrid_command( name="warn", description="Warn a member in the server.")
    async def warn(self, context: Context, member: discord.Member, reason: str = None):
        '''Warn a member in the server'''
        if self.check(context, PermissionToWarn):
            self.bot.log.info(f"{context.author.name} warned {member.name} in {context.guild.name}", context.guild)
            await self.send_message(context, member, "warned :memo:", reason, True)
            if context.guild.id not in self.warns.keys():
                self.warns[context.guild.id] = dict()
            if member.id in self.warns[context.guild.id].keys():
                self.warns[context.guild.id][member.id] += 1
            else:
                self.warns[context.guild.id][member.id] = 1
        # save the warns
        with open(os.path.join(self.bot.data_dir, str(context.guild.id), "warns.yml"), "w+") as file:
            yaml.dump(self.warns[context.guild.id], file)
    
    @commands.hybrid_command( name="removewarn", description="Remove a certain number of warns of a member in the server.")
    async def removewarn(self, context: Context, member: discord.Member, amount: int):
        '''Remove a certain number of warns of a member in the server'''
        if self.check(context, PermissionToWarn):
            if member.id in self.warns.keys():
                if self.warns[member.id] >= amount:
                    self.bot.log.info(f"{context.author.name} removed {amount} warns of {member.name} in {context.guild.name}", context.guild)
                    await self.send_message(context, member, "removed of " + str(amount) + " warns :arrow_down:", None, True)
                    if context.guild.id not in self.warns.keys():
                        self.warns[context.guild.id] = dict()
                    if member.id in self.warns[context.guild.id].keys():
                        self.warns[context.guild.id][member.id] -= amount 
                    with open(os.path.join(self.bot.data_dir, str(context.guild.id), "warns.yml"), "w+") as file:
                        yaml.dump(self.warns[context.guild.id], file)
                else:
                    self.clearwarns(context, member)

    @commands.hybrid_command( name="clearwarns", description="Clear all warns of a member in the server.")
    async def clearwarns(self, context: Context, member: discord.Member):
        '''Clear all warns of a member in the server'''
        if self.check(context, PermissionToWarn):
            if member.id in self.warns.keys():
                self.bot.log.info(f"{context.author.name} cleared all warns of {member.name} from {context.guild.name}", context.guild)
                await self.send_message(context, member, "cleared of all warns :white_check_mark:", None, False)
                if context.guild.id not in self.warns.keys():
                    self.warns[context.guild.id] = dict()
                if member.id in self.warns[context.guild.id].keys():
                    self.warns[context.guild.id][member.id] = 0
                with open(os.path.join(self.bot.data_dir, str(context.guild.id), "warns.yml"), "w+") as file:
                    yaml.dump(self.warns, file)
            else:
                embed = discord.Embed(
                    title="Warns :confused:",
                    description=f"{member.mention} has no warns.",
                    color=self.bot.default_color,
                )
                await context.send(embed=embed)
                    
    @commands.hybrid_command( name="warns", description="Get the number of warns a member has.")
    async def warns(self, context: Context, member: discord.Member):
        '''Get the number of warns a member has'''
        if self.check(context, PermissionBasic):
            if context.guild.id in self.warns.keys() and member.id in self.warns[context.guild.id].keys():
                embed = discord.Embed(
                    title="Warns :warning:",
                    description=f"{member.mention} has {self.warns[context.guild.id][member.id]} warns.",
                    color=self.bot.default_color,
                )
            else:
                embed = discord.Embed(
                    title="Warns :warning:",
                    description=f"{member.mention} has 0 warns.",
                    color=self.bot.default_color,
                )
            await context.send(embed=embed)

    def read_warns(self):
        '''Read the warns from the file'''
        if os.path.exists(os.path.join(self.bot.data_dir)):
            guilds = os.listdir(self.bot.data_dir)
            for guild_id in guilds:
                if os.path.exists(os.path.join(self.bot.data_dir, str(guild_id), "warns.yml")):
                    with open(os.path.join(self.bot.data_dir, str(guild_id), "warns.yml"), "r") as file:
                        if int(guild_id) not in self.warns.keys():
                            self.warns[int(guild_id)] = dict()
                        self.warns[int(guild_id)] = yaml.safe_load(file)
                else:
                    self.warns[int(guild_id)] = dict()
    
                 
async def setup(bot):
    await bot.add_cog(Moderation(bot))