#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Moderation commands for the bot'''

#-------------------------------------------------------------------------------

import discord
from discord.ext import commands
from discord.ext.commands import Context

class Moderation(commands.Cog, name="Moderation"):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command( name="kick", description="Kick a user from the server.")
    async def kick(self, context: Context, user: discord.Member, notify_user: bool = False, *, reason: str = None):
        # Kick user
        await user.kick(reason=reason)
        embed = discord.Embed(
            title="Kick",
            description=f"{user.mention} has been kicked by {context.author.mention}.",
            color=0xBEBEFE,
        )
        embed.add_field(
            name="Reason",
            value=reason if reason is not None else "No reason provided.",
            inline=False,
        )
        await context.send(embed=embed)
        if notify_user:
            embed = discord.Embed(
                title="Kick",
                description=f"You have been kicked from {context.guild.name}",
                color=0xBEBEFE,
            )
            embed.add_field(
                name="Reason",
                value=reason if reason is not None else "No reason provided.",
                inline=False,
            )
            await user.send(embed=embed)
        self.bot.logger.info(f"{user} has been kicked by {context.author}")
    
    @commands.hybrid_command( name="ban", description="Ban a user from the server.")
    async def ban(self, context: Context, user: discord.Member, notify_user: bool = False, *, reason: str = None):
        # Ban user
        await user.ban(reason=reason)
        embed = discord.Embed(
            title="Ban",
            description=f"{user.mention} has been banned by {context.author.mention}.",
            color=0xBEBEFE,
        )
        embed.add_field(
            name="Reason",
            value=reason if reason is not None else "No reason provided.",
            inline=False,
        )
        await context.send(embed=embed)
        if notify_user:
            embed = discord.Embed(
                title="Ban",
                description=f"You have been banned from {context.guild.name}",
                color=0xBEBEFE,
            )
            embed.add_field(
                name="Reason",
                value=reason if reason is not None else "No reason provided.",
                inline=False,
            )
            await user.send(embed=embed)
        self.bot.logger.info(f"{user} has been banned by {context.author}")
    
    @commands.hybrid_command( name="unban", description="Unban a user from the server.")
    async def unban(self, context: Context, user: discord.User, notify_user: bool = False, *, reason: str = None):
        # Unban user
        await context.guild.unban(user)
        embed = discord.Embed(
            title="Unban",
            description=f"{user.mention} has been unbanned by {context.author.mention}.",
            color=0xBEBEFE,
        )
        embed.add_field(
            name="Reason",
            value=reason if reason is not None else "No reason provided.",
            inline=False,
        )
        await context.send(embed=embed)
        if notify_user:
            embed = discord.Embed(
                title="Unban",
                description=f"You have been unbanned from {context.guild.name}",
                color=0xBEBEFE,
            )
            embed.add_field(
                name="Reason",
                value=reason if reason is not None else "No reason provided.",
                inline=False,
            )
            await user.send(embed=embed)
        self.bot.logger.info(f"{user} has been unbanned by {context.author}")
    
    @commands.hybrid_command( name="purge", description="Delete messages from a channel.")
    async def purge(self, context: Context, limit: int):
        # Purge messages
        await context.channel.purge(limit=limit)
        embed = discord.Embed(
            title="Purge",
            description=f"{limit} messages have been deleted.",
            color=0xBEBEFE,
        )
        await context.send(embed=embed)
        self.bot.logger.info(f"{limit} messages have been deleted in {context.channel.name} of {context.guild.name} by {context.author}")
    
    @commands.hybrid_command( name="mute", description="Mute a user.")
    async def mute(self, context: Context, user: discord.Member):
        # Mute user
        role = discord.utils.get(context.guild.roles, name="Muted")
        await user.add_roles(role)
        embed = discord.Embed(
            title="Mute",
            description=f"{user.mention} has been muted by {context.author.mention}.",
            color=0xBEBEFE,
        )
        await context.send(embed=embed)
        self.bot.logger.info(f"{user} has been muted by {context.author}")

    @commands.hybrid_command( name="unmute", description="Unmute a user.")
    async def unmute(self, context: Context, user: discord.Member):
        # Unmute user
        role = discord.utils.get(context.guild.roles, name="Muted")
        await user.remove_roles(role)
        embed = discord.Embed(
            title="Unmute",
            description=f"{user.mention} has been unmuted by {context.author.mention}.",
            color=0xBEBEFE,
        )
        await context.send(embed=embed)
        self.bot.logger.info(f"{user} has been unmuted by {context.author}")

    @commands.hybrid_command( name="warn", description="Warn a user.")
    async def warn(self, context: Context, user: discord.Member, notify_user: bool = False, *, reason: str = None):
        # Warn user
        # todo: ------> add a warn to the user : user.warns += 1
        embed = discord.Embed(
            title="Warn",
            description=f"{user.mention} has been warned by {context.author.mention}.",
            color=0xBEBEFE,
        )
        embed.add_field(
            name="Reason",
            value=reason if reason is not None else "No reason provided.",
            inline=False,
        )
        await context.send(embed=embed)
        if notify_user:
            embed = discord.Embed(
                title="Warn",
                description=f"You have been warned in {context.guild.name}",
                color=0xBEBEFE,
            )
            embed.add_field(
                name="Reason",
                value=reason if reason is not None else "No reason provided.",
                inline=False,
            )
            await user.send(embed=embed)
        self.bot.logger.info(f"{user} has been warned by {context.author}")

    @commands.hybrid_command(name="warns", description="Get the number of warns for a user.")
    async def warns(self, context: Context, user: discord.Member):
        # Get warns for user
        # todo: ------> get the number of warns for the user : user.
        warns = 0
        embed = discord.Embed(
            title="Warns",
            description=f"{user.mention} has {warns} warns.",
            color=0xBEBEFE,
        )
        await context.send(embed=embed)
        self.bot.logger.info(f"{user} has {warns} warns.")

    @commands.hybrid_command( name="clearwarns", description="Clear the warns for a user.")
    async def clearwarns(self, context: Context, user: discord.Member):
        # Clear warns for user
        # todo: ------> clear the warns for the user : user.warns = 0
        embed = discord.Embed(
            title="Clear Warns",
            description=f"{user.mention} warns have been cleared by {context.author.mention}.",
            color=0xBEBEFE,
        )
        await context.send(embed=embed)
        self.bot.logger.info(f"{user} warns have been cleared by {context.author}")

async def setup(bot):
    await bot.add_cog(Moderation(bot))