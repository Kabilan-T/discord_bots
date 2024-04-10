#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Greeting messages features such as welcome and goodbye messages'''

#-------------------------------------------------------------------------------

import discord
from discord.ext import commands
from discord.ext.commands import Context

class Greetings(commands.Cog, name="Greetings"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        ''' Send welcome message when a new member joins the server '''
        if member.bot:
            return
        guild = member.guild
        self.bot.log.info(f"New member {member.display_name} joined {guild.name}", guild)
        if guild.system_channel is not None:
            embed = await self.get_welcome_message(guild, member)
            await guild.system_channel.send(embed=embed)
            self.bot.log.info(f"Sending greeting message to {member.display_name} in {guild.system_channel.name}", guild)
        try:
            embed = await self.get_welcome_dm_message(guild, member)
            await member.send(embed=embed)
            self.bot.log.info(f"Sending greeting message to {member.display_name} in DM", guild)
        except discord.Forbidden:
            self.bot.log.warning(f"Failed to send greeting message to {member.display_name} in DM", guild)
            pass

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        ''' Send goodbye message when a member leaves the server '''
        if member.bot:
            return
        guild = member.guild
        self.bot.log.info(f"Member {member.display_name} left {guild.name}", guild)
        if guild.system_channel is not None:
            embed = await self.get_goodbye_message(guild, member)
            await guild.system_channel.send(embed=embed)
            self.bot.log.info(f"Sending goodbye message to {member.display_name} in {guild.system_channel.name}", guild)
        try:
            embed = await self.get_goodbye_dm_message(guild, member)
            await member.send(embed=embed)
            self.bot.log.info(f"Sending goodbye message to {member.display_name} in DM", guild)
        except discord.Forbidden:
            self.bot.log.warning(f"Failed to send goodbye message to {member.display_name} in DM", guild)
            pass

    async def get_welcome_message(self, guild: discord.Guild,  member: discord.Member):
        ''' Get welcome message for a member '''

        embed = discord.Embed()
        embed.set_author(name=self.bot.name+", The Autopilot",
                         icon_url=self.bot.user.avatar.url)
        embed.set_thumbnail(url=member.avatar.url)
        embed.title = f"Welcome to {guild.name} passenger {member.display_name}!"
        embed.description = f"Axiom is now your cosmic home. Join in, connect, and enjoy the journey! :ringed_planet: \n\n"
        embed.description += f" :flying_saucer: Passenger {member.mention} has boarded the ship! \n"
        embed.description += f" :rocket: Buckle up and Blast off!"
        embed.color = discord.Color.green()
        embed.add_field(name= f" :passport_control: Passenger count:",
                        value=f"{guild.member_count}",
                        inline=True)
        embed.add_field(name= f" :crystal_ball: Star Date:",
                        value=f"{(discord.utils.utcnow() - guild.created_at).days} days",
                        inline=True)
        embed.set_image(url="https://y.yarn.co/9e28c966-6728-47b8-9d39-8f0351b6e54a_text.gif")
        embed.set_footer(text=f"Your journey begins here @{member.name}")
        return embed
    
    async def get_goodbye_message(self, guild: discord.Guild,  member: discord.Member):
        ''' Get goodbye message for a member '''

        embed = discord.Embed()
        embed.set_author(name=self.bot.name+", The Autopilot",
                            icon_url=self.bot.user.avatar.url)
        embed.set_thumbnail(url=member.avatar.url)
        embed.title = f"Goodbye passenger {member.display_name}!"
        embed.description = f" :flying_saucer: Passenger {member.mention} has left the ship! \n"
        embed.description += f" :rocket: Hope you enjoyed your stay!"
        embed.color = discord.Color.red()
        embed.add_field(name= f" :passport_control: Passenger count:",
                        value=f"{guild.member_count}",
                        inline=True)
        embed.add_field(name= f" :crystal_ball: Journey Duration:",
                        value=f"{(discord.utils.utcnow() - member.joined_at).days} days",
                        inline=True)
        
        embed.set_footer(text=f"We will miss you @{member.name}")
        return embed
    
    async def get_welcome_dm_message(self, guild: discord.Guild,  member: discord.Member):
        ''' Get welcome message for a member '''
        embed = discord.Embed()
        embed.set_author(name=self.bot.name+", The Autopilot",
                         icon_url=self.bot.user.avatar.url)
        embed.set_thumbnail(url=member.avatar.url)
        embed.title = f"You have arrived at {guild.name} passenger {member.display_name}!"
        embed.description = f"Axiom is our cosmic home. There are {guild.member_count} passengers on board in {guild.name}. \n\n"
        embed.description += f" We welcome you with open arms and hope you enjoy your stay! \n"
        embed.description += f" :rocket: Buckle up and Blast off!"
        embed.color = discord.Color.green()
        return embed

    async def get_goodbye_dm_message(self, guild: discord.Guild,  member: discord.Member):
        ''' Get goodbye message for a member '''
        embed = discord.Embed()
        embed.set_author(name=self.bot.name+", The Autopilot",
                            icon_url=self.bot.user.avatar.url)
        embed.set_thumbnail(url=member.avatar.url)
        embed.title = f"Goodbye passenger {member.display_name}!"
        embed.description = f"We are sorry to see you leave {guild.name}. \n\n"
        embed.description += f" :rocket: Hope you enjoyed your stay!"
        embed.color = discord.Color.red()
        return embed


async def setup(bot):
    await bot.add_cog(Greetings(bot))