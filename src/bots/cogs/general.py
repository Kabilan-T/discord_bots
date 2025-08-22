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
        self.owner_id = int(os.getenv("BOT_OWNER_ID", 0))  # export BOT_OWNER_ID=[your_discord_id]
    
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
                                    value="\n".join([f"***`{command.name}`*** {' | '.join([f'**(`{alias}`)**' for alias in command.aliases]) if command.aliases else ''} - {command.description}"for command in cog_commands  if not command.hidden]),
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
    @commands.has_permissions(moderate_members=True)
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
    @commands.has_permissions(moderate_members=True)
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
    @commands.has_permissions(send_messages=True)
    async def invite(self, context: Context):
        '''Send the bot invite link with permissions scope'''
        permission_scope = 1759218604441591  # All permissions except administrator
        embed = discord.Embed(
            title="Invite",
            description=f"Use this link to invite the bot to your server: https://discord.com/oauth2/authorize?client_id={self.bot.client_id}&scope=bot&permissions={permission_scope}",
            color=self.bot.default_color,
            )
        await context.send(embed=embed)

    @commands.command(name="about", description="Get information about the bot.")
    @commands.has_permissions(send_messages=True)
    async def about(self, context: Context):
        """Send information about the bot"""
        repository_url = "https://github.com/Kabilan-T/discord_bots"
        embed = discord.Embed(
            title="About",
            description = (
                f"**{self.bot.name}** is a Discord bot developed as part of the "
                f"[Discord Bots Project]({repository_url}). "
                "It is designed to provide various custom and novel features for a bot.\n\n"
                "As a hobby project, the bot may occasionally encounter bugs or unexpected behavior, "
                "but contributions are always welcomed 🙂\n\n"
                f"To know more, visit the repository here: [discord_bots]({repository_url}?tab=readme-ov-file#discord-bots)"
            ),
            color=self.bot.default_color,
        )
        await context.send(embed=embed)

    @commands.command(name="feedback", description="Send feedback to the bot developer.")
    @commands.has_permissions(send_messages=True)
    async def feedback(self, context: Context, *, message: str):
        '''Send feedback to the bot developer.'''
        feedback = discord.Embed(
            title="Feedback",
            description=message,
            color=self.bot.default_color,
        )
        feedback.add_field(name="User", value=f"{context.author.name} (ID: `{context.author.id}`)", inline=False)
        if context.guild:
            feedback.add_field(name="Guild", value=f"{context.guild.name} (ID: `{context.guild.id}`)", inline=False)
            feedback.add_field(name="Channel", value=f"{context.channel.name} (ID: `{context.channel.id}`)", inline=False)
            feedback.add_field(name="Message", value=f"ID: `{context.message.id}`", inline=False)
            feedback.add_field(name="Respond_with", value=f"`{self.bot.default_prefix}respond {context.guild.id} {context.channel.id} {context.message.id} <response>`", inline=False)
        # Default success embed if owner cannot be contacted
        embed_default = discord.Embed(
            title="Thank You!",
            description="Your feedback is logged.",
            color=self.bot.default_color,
        )
        # If owner exists, try sending DM
        if self.owner_id:
            try:
                owner = await self.bot.fetch_user(self.owner_id)
                if owner:
                    await owner.send(embed=feedback)
                    embed_success = discord.Embed(
                        title="Thank You!",
                        description="Your feedback has been sent to the bot developer. They might respond to it if needed.",
                        color=self.bot.default_color,
                    )
                    self.bot.log.info(f"Feedback from {context.author.name} (ID: {context.author.id}) sent to the owner.", guild=context.guild)
                    await context.send(embed=embed_success)
                    return
            except discord.Forbidden:
                pass
            except discord.HTTPException:
                pass
        # Fallback if owner not set or DM failed
        self.bot.log.warning(f"Feedback from {context.author.name} (ID: {context.author.id}) could not be sent to the owner.\n{feedback.to_dict()}",guild=context.guild)
        await context.send(embed=embed_default)

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