#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' General commands for the bot'''

#-------------------------------------------------------------------------------

import discord
from discord.ext import commands
from discord.ext.commands import Context


class General(commands.Cog, name="General"):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command( name="help", description="Get help on a command.")
    async def help(self, context: Context, command: str = None):
        # Send help message
        if command is None:
            embed = discord.Embed(
                title="Help",
                description=f"Use `{self.bot.prefix}help <command>` for more info on a command.",
                color=0xBEBEFE,
            )
            for cog in self.bot.cogs:
                cog_commands = self.bot.get_cog(cog).get_commands()
                if len(cog_commands) > 0:
                    embed.add_field(
                        name=cog,
                        value=", ".join([f"`{command.name}`" for command in cog_commands]),
                        inline=False,
                    )
            await context.send(embed=embed)
        else:
            command = self.bot.get_command(command)
            if command is None:
                embed = discord.Embed(
                    title="Help",
                    description=f"`{command}` is not a valid command.",
                    color=0xBEBEFE,
                )
                await context.send(embed=embed)
            else:
                embed = discord.Embed(
                    title=f"Help: {command.name}",
                    description=command.description,
                    color=0xBEBEFE,
                )
                embed.add_field(
                    name="Usage",
                    value=f"`{self.bot.prefix}{command.name} {command.signature}`",
                    inline=False,
                )
                await context.send(embed=embed)

    @commands.hybrid_command( name="hello", description="Say hello to the bot.")
    async def hello(self, context: Context):
        # Send a greeting message to the user
        embed = discord.Embed(
            title="Hello "+context.author.name+" :wave:",
            description=f"I am {self.bot.name}, a discord bot. Nice to meet you! :smile:",
            color=0xBEBEFE,
        )
        await context.send(embed=embed)

    @commands.hybrid_command( name="ping", description="Check if the bot is alive.")
    async def ping(self, context: Context):
        # Check if the bot is active and send the latency
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"The bot latency is {round(self.bot.latency * 1000)}ms.",
            color=0xBEBEFE,
        )
        await context.send(embed=embed)

    @commands.hybrid_command( name="invite", description="Get the bot invite link.")
    async def invite(self, context: Context):
        #  Send the bot invite link with permissions of admin
        embed = discord.Embed(
            title="Invite",
            description=f"Use this link to invite the bot to your server: https://discord.com/oauth2/authorize?client_id={self.bot.client_id}&scope=bot&permissions=8",
            color=0xBEBEFE,
        )
        await context.send(embed=embed)

    @commands.hybrid_command( name="prefix", description="Change the bot prefix.")
    async def prefix(self, context: Context, prefix: str = None):
        # Change the bot prefix
        if prefix is None:
            embed = discord.Embed(
                title="Prefix",
                description=f"The current prefix is `{self.bot.prefix}`",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
        else:
            self.bot.prefix = prefix
            embed = discord.Embed(
                title="Prefix",
                description=f"The prefix has been changed to `{self.bot.prefix}`",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
            self.bot.logger.info(f"Prefix changed to {self.bot.prefix}")
    
async def setup(bot):
    await bot.add_cog(General(bot))
    

        