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
        guild = member.guild

        title = f"Welcome to {guild.name} passenger {member.name}!"
        description = f"Axiom is now your cosmic home. Join in, connect, and enjoy the journey! :ringed_planet: \n\n"
        description += f" :flying_saucer::Passenger {member.mention} has boarded the ship!"
        description += f" :passport_control: Passenger count: {guild.member_count}"
        description += f" :rocket: Buckle up and Blast off!"                                                                           
        embed = discord.Embed(title=title,
                              description=description,
                              color=discord.Color.green())
        embed.set_author(name=self.bot.name+", The Autopilot",
                            icon_url=self.bot.user.avatar_url)
        embed.set_thumbnail(url=member.avatar_url)
        embed.set_image(url="https://y.yarn.co/9e28c966-6728-47b8-9d39-8f0351b6e54a_text.gif")

        if guild.system_channel is not None:
            await guild.system_channel.send(embed=embed)



    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        ''' Send goodbye message when a member leaves the server '''
        guild = member.guild

        title = f"Goodbye passenger {member.name}!"
        description = f" :flying_saucer: Passenger {member.mention} has left the ship!"
        description += f" :passport_control: Passenger count: {guild.member_count}"
        description += f" :rocket: Hope you enjoyed your stay!"
        embed = discord.Embed(title=title,
                              description=description,
                              color=discord.Color.red())
        embed.set_author(name=self.bot.name+", The Autopilot",
                            icon_url=self.bot.user.avatar_url)
        embed.set_thumbnail(url=member.avatar_url)
        
        if guild.system_channel is not None:
            await guild.system_channel.send(embed=embed)
            

async def setup(bot):
    bot.add_cog(Greetings(bot))