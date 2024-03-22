#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Moderation commands for the bot'''

#-------------------------------------------------------------------------------

import os
import yaml
import discord
from discord.ext import commands
from discord.ext.commands import Context


# Default permissions : Change 
PermissionToBan = discord.Permissions(ban_members=True)
PermissionToWarn = discord.Permissions(ban_members=True)
PermissionToKick = discord.Permissions(kick_members=True)
PermissionToMute = discord.Permissions(mute_members=True)
PermissionToDeafen = discord.Permissions(deafen_members=True)
PermissionToPurge = discord.Permissions(manage_messages=True)
PermissionBasic = discord.Permissions(send_messages=True)

warn_list_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "warns.yml")

class Moderation(commands.Cog, name="Moderation"):
    def __init__(self, bot):
        self.bot = bot
        self.warns = yaml.load(open(warn_list_file, "r"), Loader=yaml.FullLoader) if os.path.exists(warn_list_file) else dict()

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
            if member.id in self.warns.keys():
                self.warns[member.id] += 1
            else:
                self.warns[member.id] = 1
        # save the warns
        with open(warn_list_file, "w+") as file:
            yaml.dump(self.warns, file)

    
    @commands.hybrid_command( name="removewarn", description="Remove a certain number of warns of a member in the server.")
    async def removewarn(self, context: Context, member: discord.Member, amount: int):
        '''Remove a certain number of warns of a member in the server'''
        if self.check(context, PermissionToWarn):
            if member.id in self.warns.keys():
                if self.warns[member.id] >= amount:
                    self.bot.log.info(f"{context.author.name} removed {amount} warns of {member.name} in {context.guild.name}", context.guild)
                    await self.send_message(context, member, "removed of " + str(amount) + " warns :arrow_down:", None, True)
                    self.warns[member.id] -= amount
                    with open(warn_list_file, "w+") as file:
                        yaml.dump(self.warns, file)
                else:
                    self.clearwarns(context, member)
            

    @commands.hybrid_command( name="clearwarns", description="Clear all warns of a member in the server.")
    async def clearwarns(self, context: Context, member: discord.Member):
        '''Clear all warns of a member in the server'''
        if self.check(context, PermissionToWarn):
            if member.id in self.warns.keys():
                self.bot.log.info(f"{context.author.name} cleared all warns of {member.name} from {context.guild.name}", context.guild)
                await self.send_message(context, member, "cleared of all warns :white_check_mark:", None, False)
                self.warns[member.id] = 0
                with open(warn_list_file, "w+") as file:
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
            if member.id in self.warns.keys():
                embed = discord.Embed(
                    title="Warns :warning:",
                    description=f"{member.mention} has {self.warns[member.id]} warns.",
                    color=self.bot.default_color,
                )
            else:
                embed = discord.Embed(
                    title="Warns :warning:",
                    description=f"{member.mention} has 0 warns.",
                    color=self.bot.default_color,
                )
            await context.send(embed=embed)
    
                 
async def setup(bot):
    await bot.add_cog(Moderation(bot))