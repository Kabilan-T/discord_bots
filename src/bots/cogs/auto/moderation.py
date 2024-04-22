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
import typing
import datetime
from discord.ext import commands
from discord.ext.commands import Context


# Default permissions : Change 
PermissionToBan = discord.Permissions(ban_members=True)
PermissionToTimeOut = discord.Permissions(moderate_members=True)
PermissionToWarn = discord.Permissions(moderate_members=True)
PermissionToKick = discord.Permissions(kick_members=True)
PermissionToMute = discord.Permissions(mute_members=True)
PermissionToDeafen = discord.Permissions(deafen_members=True)
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
        except discord.DiscordException:
            self.bot.log.warning(f"Could not send DM to @{member.name} about {action} activity in {context.guild.name}", context.guild)
            pass
    
    @commands.command( name="mute", description="Mute a member in the server.")
    async def mute(self, context: Context, member: discord.Member, *, reason: str = None):
        '''Mute a member in the server'''
        if not self.check(context, PermissionToMute): return
        if member.voice is None:
            embed = discord.Embed(
                title="Mute :confused:",
                description=f"{member.mention} is not in a voice channel.",
                color=self.bot.default_color,
                )
            await context.send(embed=embed)
            return
        await member.edit(mute=True, reason=reason)
        self.bot.log.info(f"{context.author.name} muted {member.name} in {context.guild.name}", context.guild)
        embed = discord.Embed(
            title="Moderation activity - Mute :mute:",
            description=f"**{member.mention}** has been muted by **{context.author.mention}**.",
            color=self.bot.default_color,
            )
        if reason is not None: embed.add_field(name="Reason", value=reason, inline=False)
        await context.send(embed=embed)
    
    @commands.command( name="unmute", description="Unmute a member in the server.")
    async def unmute(self, context: Context, member: discord.Member, *, reason: str = None):
        '''Unmute a member in the server'''
        if not self.check(context, PermissionToMute): return
        if member.voice is None:
            embed = discord.Embed(
                title="Unmute :confused:",
                description=f"{member.mention} is not in a voice channel.",
                color=self.bot.default_color,
                )
            await context.send(embed=embed)
            return
        await member.edit(mute=False, reason=reason)
        self.bot.log.info(f"{context.author.name} unmuted {member.name} in {context.guild.name}", context.guild)
        embed = discord.Embed(
            title="Moderation activity - Unmute :loud_sound:",
            description=f"**{member.mention}** has been unmuted by **{context.author.mention}**.",
            color=self.bot.default_color,
            )
        if reason is not None: embed.add_field(name="Reason", value=reason, inline=False)
        await context.send(embed=embed)
    
    @commands.command( name="deafen", description="Deafen a member in the server.")
    async def deafen(self, context: Context, member: discord.Member, *, reason: str = None):
        '''Deafen a member in the server'''
        if not self.check(context, PermissionToDeafen): return
        if member.voice is None:
            embed = discord.Embed(
                title="Deafen :confused:",
                description=f"{member.mention} is not in a voice channel.",
                color=self.bot.default_color,
                )
            await context.send(embed=embed)
            return
        await member.edit(deafen=True, reason=reason)
        self.bot.log.info(f"{context.author.name} deafened {member.name} in {context.guild.name}", context.guild)
        embed = discord.Embed(
            title="Moderation activity - Deafen :ear_with_hearing_aid:",
            description=f"**{member.mention}** has been deafened by **{context.author.mention}**.",
            color=self.bot.default_color,
            )
        if reason is not None: embed.add_field(name="Reason", value=reason, inline=False)
        await context.send(embed=embed)
    
    @commands.command( name="undeafen", description="Undeafen a member in the server.")
    async def undeafen(self, context: Context, member: discord.Member, *, reason: str = None):
        '''Undeafen a member in the server'''
        if not self.check(context, PermissionToDeafen): return
        if member.voice is None:
            embed = discord.Embed(
                title="Undeafen :confused:",
                description=f"{member.mention} is not in a voice channel.",
                color=self.bot.default_color,
                )
            await context.send(embed=embed)
            return
        await member.edit(deafen=False, reason=reason)
        self.bot.log.info(f"{context.author.name} undeafened {member.name} in {context.guild.name}", context.guild)
        embed = discord.Embed(
            title="Moderation activity - Undeafen :ear:",
            description=f"**{member.mention}** has been undeafened by **{context.author.mention}**.",
            color=self.bot.default_color,
            )
        if reason is not None: embed.add_field(name="Reason", value=reason, inline=False)
        await context.send(embed=embed)
    
    @commands.command( name="timeout", description="Timeout a member in the server.")
    async def timeout(self, context: Context, member: discord.Member, duration: int, *, reason: str = None):
        '''Timeout a member in the server'''
        if not self.check(context, PermissionToTimeOut): return
        duration = datetime.timedelta(minutes=duration)
        await member.timeout(duration, reason=reason)
        self.bot.log.info(f"{context.author.name} timed out {member.name} in {context.guild.name}", context.guild)
        embed = discord.Embed(
            title="Moderation activity - Timeout :hourglass_flowing_sand:",
            description=f"**{member.mention}** has been timed out by **{context.author.mention}**.",
            color=self.bot.default_color,
            )
        if reason is not None: embed.add_field(name="Reason", value=reason, inline=False)
        await context.send(embed=embed)
    
    @commands.command( name="remove_timeout", description="Remove the timeout of a member in the server.")
    async def removetimeout(self, context: Context, member: discord.Member, *, reason: str = None):
        '''Remove the timeout of a member in the server'''
        if not self.check(context, PermissionToTimeOut): return
        await member.timeout(None)
        self.bot.log.info(f"{context.author.name} removed timeout of {member.name} in {context.guild.name}", context.guild)
        embed = discord.Embed(
            title="Moderation activity - Remove Timeout :hourglass:",
            description=f"**{member.mention}** has been removed timeout by **{context.author.mention}**.",
            color=self.bot.default_color,
            )
        if reason is not None: embed.add_field(name="Reason", value=reason, inline=False)
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
    
    def save_warns(self, guild_id: int):
        '''Save the warns to the file'''
        if not os.path.exists(os.path.join(self.bot.data_dir, str(guild_id))):
            os.makedirs(os.path.join(self.bot.data_dir, str(guild_id)))
        with open(os.path.join(self.bot.data_dir, str(guild_id), "warns.yml"), "w+") as file:
            yaml.dump(self.warns[guild_id], file)
    
    def delete_warns_file(self, guild_id: int):
        '''Delete the warns file'''
        if os.path.exists(os.path.join(self.bot.data_dir, str(guild_id), "warns.yml")):
            os.remove(os.path.join(self.bot.data_dir, str(guild_id), "warns.yml"))
    
    @commands.command( name="warn", description="Warn a member in the server.")
    async def warn(self, context: Context, member: discord.Member, *, reason: str = None):
        '''Warn a member in the server'''
        if not self.check(context, PermissionToWarn): return
        if context.guild.id not in self.warns.keys():
            self.warns[context.guild.id] = dict()
        if member.id in self.warns[context.guild.id].keys():
            self.warns[context.guild.id][member.id] += 1
        else:
            self.warns[context.guild.id][member.id] = 1
        self.bot.log.info(f"{context.author.name} warned {member.name} in {context.guild.name}", context.guild)
        self.save_warns(context.guild.id)
        embed = discord.Embed(
            title="Moderation activity - Warn :warning:",
            description=f"**{member.mention}** has been warned by **{context.author.mention}**.",
            color=self.bot.default_color,
            )
        if reason is not None: embed.add_field(name="Reason", value=reason, inline=False)
        await context.send(embed=embed)
        await self.send_dm(context, member, "warned", reason)
     
    @commands.command( name="check_warns", description="Check the number of warns of one or all members in the server.")
    async def check_warns(self, context: Context, member: typing.Optional[discord.Member] = None):
        '''Check the number of warns of one or all members in the server'''
        if not self.check(context, PermissionBasic): return
        if context.guild.id in self.warns.keys():
            guild_warns = self.warns[context.guild.id].copy()
            for member_id, warns in guild_warns.items():
                if warns == 0: del self.warns[context.guild.id][member_id]
            if len(self.warns[context.guild.id]) == 0:
                del self.warns[context.guild.id]
                self.delete_warns_file(context.guild.id)
            else:
                self.save_warns(context.guild.id)
        if context.guild.id not in self.warns.keys():
            embed = discord.Embed(
                title="Warns :warning:",
                description="No members have warns.",
                color=self.bot.default_color,
                )
            await context.send(embed=embed)
            return
        embed = discord.Embed(
            title="Warns :warning:",
            description="",
            color=self.bot.default_color,
            )
        if member is None:
            self.bot.log.info(f"{context.author.name} checked the warns of all members in {context.guild.name}", context.guild)
            for member_id in self.warns[context.guild.id].keys():
                member = context.guild.get_member(member_id)
                if member is not None:
                    embed.description += f"{member.mention} has {self.warns[context.guild.id][member_id]} warns.\n"
                else:
                    embed.description += f"Member with ID {member_id} has {self.warns[context.guild.id][member_id]} warns.\n"
        else:
            self.bot.log.info(f"{context.author.name} checked the warns of {member.name} in {context.guild.name}", context.guild)
            if member.id in self.warns[context.guild.id].keys():
                embed.description += f"{member.mention} has {self.warns[context.guild.id][member.id]} warns."
            else:
                embed.description += f"{member.mention} has no warns."
        await context.send(embed=embed)

    @commands.command( name="remove_warn", description="Remove a certain number of warns of a member in the server.")
    async def removewarn(self, context: Context, member: typing.Union[discord.Member, int], amount: int, *, reason: str = None):
        '''Remove a certain number of warns of a member in the server'''
        if not self.check(context, PermissionToWarn): return
        if context.guild.id not in self.warns.keys():
            self.warns[context.guild.id] = dict()
        if isinstance(member, int):
            member = self.bot.fetch_user(member)
        if member.id not in self.warns[context.guild.id].keys():
            embed = discord.Embed(
                title="Warns :confused:",
                description=f"{member.mention} has no warns.",
                color=self.bot.default_color,
                )
            await context.send(embed=embed)
            return
        if self.warns[context.guild.id][member.id] >= amount:
            self.warns[context.guild.id][member.id] -= amount 
            if self.warns[context.guild.id][member.id] == 0:
                del self.warns[context.guild.id][member.id]
            if len(self.warns[context.guild.id]) == 0:
                del self.warns[context.guild.id]
                self.delete_warns_file(context.guild.id)
            else:
                self.save_warns(context.guild.id)
            self.bot.log.info(f"{context.author.name} removed {amount} warns of {member.name} in {context.guild.name}", context.guild)
            embed = discord.Embed(
                title="Moderation activity - Remove Warn :arrow_down:",
                description=f"**{amount}** warns have been removed from **{member.mention}** by **{context.author.mention}**.",
                color=self.bot.default_color,
                )
            if reason is not None: embed.add_field(name="Reason", value=reason, inline=False)
            await context.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Warns :confused:",
                description=f"{member.mention} has only {self.warns[context.guild.id][member.id]} warns.",
                color=self.bot.default_color,
                )
            await context.send(embed=embed)
            await self.send_dm(context, member, "removed " + str(amount) + " warns", reason)
        
    @commands.command( name="clear_warns", description="Clear all warns of a member in the server.")
    async def clearwarns(self, context: Context, member: typing.Union[discord.Member, int], *, reason: str = None):
        '''Clear all warns of a member in the server'''
        if not self.check(context, PermissionToWarn): return
        if context.guild.id not in self.warns.keys():
            self.warns[context.guild.id] = dict()
        if isinstance(member, int):
            member = await self.bot.fetch_user(member)
        if member.id not in self.warns[context.guild.id].keys():
            embed = discord.Embed(
                title="Warns :confused:",
                description=f"{member.mention} has no warns.",
                color=self.bot.default_color,
                )
            await context.send(embed=embed)
            return
        self.warns[context.guild.id][member.id] = 0
        del self.warns[context.guild.id][member.id]
        if len(self.warns[context.guild.id]) == 0:
            del self.warns[context.guild.id]
            self.delete_warns_file(context.guild.id)
        else:
            self.save_warns(context.guild.id)
        self.bot.log.info(f"{context.author.name} cleared all warns of {member.name} from {context.guild.name}", context.guild)
        embed = discord.Embed(
            title="Moderation activity - Clear Warns :white_check_mark:",
            description=f"All warns have been cleared for **{member.mention}** by **{context.author.mention}**.",
            color=self.bot.default_color,
            )
        if reason is not None: embed.add_field(name="Reason", value=reason, inline=False)
        await context.send(embed=embed)
        await self.send_dm(context, member, "cleared all warns", reason)

    @commands.command( name="kick", description="Kick a member from the server.")
    async def kick(self, context: Context, member: discord.Member, *, reason: str = None):
        '''Kick a member from the server'''
        if not self.check(context, PermissionToKick): return
        await member.kick(reason=reason)
        self.bot.log.info(f"{context.author.name} kicked {member.name} from {context.guild.name}", context.guild)
        await self.send_dm(context, member, "kicked", reason)
        embed = discord.Embed(
            title="Moderation activity - Kick :boxing_glove:",
            description=f"**{member.mention}** has been kicked by **{context.author.mention}**.",
            color=self.bot.default_color,
            )
        if reason is not None: embed.add_field(name="Reason", value=reason, inline=False)
        await context.send(embed=embed)
    
    @commands.command( name="softban", description="Softban a member from the server.")
    async def softban(self, context: Context, member: discord.Member, *, reason: str = None):
        '''Softban a member from the server'''
        if not self.check(context, PermissionToBan): return
        member_id = member.id
        await member.ban(reason=reason)
        member = await self.bot.fetch_user(member_id)
        await context.guild.unban(member, reason=reason)
        self.bot.log.info(f"{context.author.name} softbanned {member.name} from {context.guild.name}", context.guild)
        await self.send_dm(context, member, "softbanned", reason)
        embed = discord.Embed(
            title="Moderation activity - Softban :no_entry:",
            description=f"**{member.mention}** has been softbanned by **{context.author.mention}**.",
            color=self.bot.default_color,
            )
        if reason is not None: embed.add_field(name="Reason", value=reason, inline=False)
        await context.send(embed=embed)

    @commands.command( name="ban", description="Ban a member from the server.")
    async def ban(self, context: Context, member: discord.Member, *, reason: str = None):
        '''Ban a member from the server'''
        if not self.check(context, PermissionToBan): return
        await member.ban(reason=reason)
        self.bot.log.info(f"{context.author.name} banned {member.name} from {context.guild.name}", context.guild)
        await self.send_dm(context, member, "banned", reason)
        embed = discord.Embed(
            title="Moderation activity - Ban :no_entry:",
            description=f"**{member.mention}** has been banned by **{context.author.mention}**.",
            color=self.bot.default_color,
            )
        if reason is not None: embed.add_field(name="Reason", value=reason, inline=False)
        await context.send(embed=embed)

    @commands.command( name="unban", description="Unban a member from the server.")
    async def unban(self, context: Context, member_id: int, *, reason: str = None):
        '''Unban a member from the server'''
        if not self.check(context, PermissionToBan): return
        member = await self.bot.fetch_user(member_id)
        await context.guild.unban(member, reason=reason)
        self.bot.log.info(f"{context.author.name} unbanned {member.name} in {context.guild.name}", context.guild)
        await self.send_dm(context, member, "unbanned", reason)
        embed = discord.Embed(
            title="Moderation activity - Unban :unlock:",
            description=f"**{member.mention}** has been unbanned by **{context.author.mention}**.",
            color=self.bot.default_color,
            )
        if reason is not None: embed.add_field(name="Reason", value=reason, inline=False)
        await context.send(embed=embed)

                 
async def setup(bot):
    await bot.add_cog(Moderation(bot))