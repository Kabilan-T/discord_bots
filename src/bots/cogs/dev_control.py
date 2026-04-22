#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Developer control cog for the bot '''

#-------------------------------------------------------------------------------

import os
import io
import discord
from discord.ext import commands
from discord.ext.commands import Context


class DevControl(commands.Cog, name="Developer Control"):
    def __init__(self, bot):
        '''Initializes the developer control cog'''
        self.bot = bot
        self.owner_id = int(os.getenv("BOT_OWNER_ID", 0))  # export BOT_OWNER_ID=[your_discord_id]

    @commands.command(name="respond_to_feedback", description="Respond to a feedback message.", aliases=["respond"], hidden=True)
    async def respond_to_feedback(self, context: Context, guild_id: int, channel_id: int, message_id: int, *, response: str):
        '''Respond to a feedback message.'''
        # Only allow the bot owner to use this command
        if context.author.id != self.owner_id:
            embed = discord.Embed(
                title="Unauthorized",
                description="You are not authorized to use this command.",
                color=discord.Color.red()
            )
            await context.send(embed=embed)
            return
        channel = self.bot.get_channel(channel_id)
        reply_embed = discord.Embed(
            title="Response from the Developer",
            description=response,
            color=self.bot.default_color
        )
        confirm_embed = discord.Embed(
            title="Response to Feedback",
            color=self.bot.default_color
        )
        if not channel:
            confirm_embed.description = "The feedback channel could not be found."
            await context.send(embed=confirm_embed)
            return
        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            confirm_embed.description = "The feedback message could not be found."
            await context.send(embed=confirm_embed)
            return
        except discord.Forbidden:
            confirm_embed.description = "I cannot access that channel."
            await context.send(embed=confirm_embed)
            return
        # Send the embed reply to the feedback message
        await message.reply(embed=reply_embed)
        confirm_embed.description = f"Your reply has been sent to the feedback message (`{message_id}`)."
        await context.send(embed=confirm_embed)
        # Confirmation embed for the owner
        confirm_embed = discord.Embed(
            title="Response Sent",
            description=f"Your reply has been sent to the feedback message (`{message_id}`).",
            color=discord.Color.blue()
        )
        await context.send(embed=confirm_embed)

    @commands.command(name="fetch_guilds", description="Fetch all guilds the bot is in. Developer only command.", aliases=["fetch_glds"], hidden=True)
    async def fetch_guilds(self, context: Context):
        '''Fetch all guilds the bot is in. Developer only command.'''
        # Only allow the bot owner to use this command
        if context.author.id != self.owner_id:
            embed = discord.Embed(
                title="Unauthorized",
                description="You are not authorized to use this command.",
                color=discord.Color.red()
            )
            await context.send(embed=embed)
            return
        guilds_info = []
        for guild in self.bot.guilds:
            guilds_info.append(f"{guild.name} (ID: `{guild.id}`) - Members: {guild.member_count}")
        guilds_text = "\n".join(guilds_info)
        if len(guilds_text) > 2000:
            # If the text exceeds Discord's message limit, send it as a file
            file = discord.File(io.StringIO(guilds_text), filename="guilds.txt")
            await context.send(file=file)
        else:
            embed = discord.Embed(
                title="Guilds",
                description=guilds_text,
                color=self.bot.default_color
            )
            await context.send(embed=embed)

    @commands.command(name="developer_announcement", description="Send an announcement to a specified channel in a specified guild. Developer only command.", aliases=["dev_announce"], hidden=True)
    async def developer_announcement(self, context: Context, guild_id: int, channel_id: int, title: str, *, message: str):
        '''Send an announcement to a specified channel in a specified guild. Developer only command.'''
        # Only allow the bot owner to use this command
        if context.author.id != self.owner_id:
            embed = discord.Embed(
                title="Unauthorized",
                description="You are not authorized to use this command.",
                color=discord.Color.red()
            )
            await context.send(embed=embed)
            return
        guild = self.bot.get_guild(guild_id)
        if not guild:
            embed = discord.Embed(
                title="Error",
                description="The specified guild could not be found.",
                color=discord.Color.red()
            )
            await context.send(embed=embed)
            return
        channel = guild.get_channel(channel_id)
        if not channel:
            embed = discord.Embed(
                title="Error",
                description="The specified channel could not be found in the specified guild.",
                color=discord.Color.red()
            )
            await context.send(embed=embed)
            return
        announcement_embed = discord.Embed(
            title=title,
            description=message,
            color=self.bot.default_color
        )
        try:
            await channel.send(embed=announcement_embed)
            embed = discord.Embed(
                title="Announcement Sent",
                description=f"Your announcement has been sent to {channel.mention} in {guild.name}.",
                color=discord.Color.green()
            )
            await context.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(
                title="Error",
                description="I do not have permission to send messages in the specified channel.",
                color=discord.Color.red()
            )
            await context.send(embed=embed)

    @commands.command(name="fetch_channels", description="Fetch all channels in a specified guild. Developer only command.", aliases=["fetch_chans"], hidden=True)
    async def fetch_channels(self, context: Context, guild_id: int):
        '''Fetch all channels in a specified guild. Developer only command.'''
        # Only allow the bot owner to use this command
        if context.author.id != self.owner_id:
            embed = discord.Embed(
                title="Unauthorized",
                description="You are not authorized to use this command.",
                color=discord.Color.red()
            )
            await context.send(embed=embed)
            return
        guild = self.bot.get_guild(guild_id)
        if not guild:
            embed = discord.Embed(
                title="Error",
                description="The specified guild could not be found.",
                color=discord.Color.red()
            )
            await context.send(embed=embed)
            return
        channels_info = []
        for channel in guild.channels:
            channels_info.append(f"{channel.name} (ID: `{channel.id}`) - Type: {str(channel.type)}")
        channels_text = "\n".join(channels_info)
        if len(channels_text) > 2000:
            # If the text exceeds Discord's message limit, send it as a file
            file = discord.File(io.StringIO(channels_text), filename=f"{guild.name}_channels.txt")
            await context.send(file=file)
        else:
            embed = discord.Embed(
                title=f"Channels in {guild.name}",
                description=channels_text,
                color=self.bot.default_color
            )
            await context.send(embed=embed)

    @commands.command(name="fetch_messages", description="Fetch recent messages from a specified channel. Developer only command.", aliases=["fetch_msgs"], hidden=True)
    async def fetch_messages(self, context: Context, guild_id: int, channel_id: int, limit: int = 100):
        '''Fetch recent messages from a specified channel. Developer only command.'''
        # Only allow the bot owner to use this command
        if context.author.id != self.owner_id:
            embed = discord.Embed(
                title="Unauthorized",
                description="You are not authorized to use this command.",
                color=discord.Color.red()
            )
            await context.send(embed=embed)
            return
        guild = self.bot.get_guild(guild_id)
        if not guild:
            embed = discord.Embed(
                title="Error",
                description="The specified guild could not be found.",
                color=discord.Color.red()
            )
            await context.send(embed=embed)
            return
        channel = guild.get_channel(channel_id)
        if not channel:
            embed = discord.Embed(
                title="Error",
                description="The specified channel could not be found in the specified guild.",
                color=discord.Color.red()
            )
            await context.send(embed=embed)
            return
        messages_info = []
        try:
            async for message in channel.history(limit=limit):
                messages_info.append(f"{message.author.name} (ID: `{message.author.id}`): {message.content} (ID: `{message.id}`)")
        except discord.Forbidden:
            embed = discord.Embed(
                title="Error",
                description="I do not have permission to read messages in the specified channel.",
                color=discord.Color.red()
            )
            await context.send(embed=embed)
            return
        messages_text = "\n".join(messages_info)
        if len(messages_text) > 2000:
            # If the text exceeds Discord's message limit, send it as a file
            file = discord.File(io.StringIO(messages_text), filename=f"{channel.name}_messages.txt")
            await context.send(file=file)
        else:
            embed = discord.Embed(
                title=f"Recent Messages in {channel.name}",
                description=messages_text,
                color=self.bot.default_color
            )
            await context.send(embed=embed)
    
async def setup(bot):
    await bot.add_cog(DevControl(bot))    