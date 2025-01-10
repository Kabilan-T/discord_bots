#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Announcements messages for server and DMs '''

#-------------------------------------------------------------------------------

import os
import yaml
import discord
import typing
import datetime
from discord.ext import tasks
from discord.ext import commands
from discord.ext.commands import Context

class Announcements(commands.Cog, name="Announcements"):
    def __init__(self, bot):
        self.bot = bot
        if self.broadcast_daily_highlights.is_running():
            self.bot.log.info("broadcast_daily_highlights task is already running")
            self.broadcast_daily_highlights.stop()
            self.bot.log.info("broadcast_daily_highlights task stopped")
        self.broadcast_daily_highlights.start()
    
    @tasks.loop(time=datetime.time(hour=0, minute=0, second=0, tzinfo=datetime.timezone.utc))
    async def broadcast_daily_highlights(self):
        ''' Broadcast daily highlights to all servers '''
        today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        holiday_data = self.load_holiday_data()
        if holiday_data is None: return
        todays_events = holiday_data.get(today, None)
        if todays_events is None:
            self.bot.log.info(f"No special events found for {today}")
            return
        embed = discord.Embed(
            title="Today's Highlights :calendar_spiral:",
            color=self.bot.default_color,
            )
        for event in todays_events:
            event_name = event['name']
            event_description = event['description']
            event_type = event['types']
            embed.add_field(name=f"**{event_name}**",
                            value=f"_{event_description}_\ncategory: _{event_type}_\n",
                            inline=False)
        for guild in self.bot.guilds:
            general_channel = discord.utils.find( lambda c: "general" in c.name.lower(), guild.text_channels)
            if general_channel is not None:
                embed.set_author(name=self.bot.name+", The Autopilot", icon_url=self.bot.user.avatar.url)
                embed.set_footer(text=f"Earth Date: {today} \t\t\t\tStar Date: {(discord.utils.utcnow() - guild.created_at).days} days")
                await general_channel.send(embed=embed)
                self.bot.log.info(f"Sending today's highlights to {guild.name} in {general_channel.name}", guild)
            else:
                self.bot.log.warning(f"No general channel found in {guild.name}", guild)
    
    @broadcast_daily_highlights.before_loop
    async def before_broadcast(self):
        await self.bot.wait_until_ready()
    
    def cog_unload(self):
        self.broadcast_daily_highlights.cancel()
        
    def load_holiday_data(self):
        ''' Load holidays data from file '''
        data_fpath = os.path.join(self.bot.data_dir, "holidays_2025.yml")
        if not os.path.exists(data_fpath):
            self.bot.log.warning(f"Holidays file not found in {data_fpath}")
            return None
        try:
            with open(data_fpath, "r") as file:
                holidays = yaml.load(file, Loader=yaml.FullLoader) or None
            self.bot.log.info(f"Loaded {len(holidays)} holidays from {data_fpath}")
            return holidays
        except Exception as e:
            self.bot.log.warning(f"Error loading holidays: {e}")
            return None

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        ''' Send welcome message when a new member joins the server '''
        if member.bot: return
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
        if member.bot: return
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
    await bot.add_cog(Announcements(bot))