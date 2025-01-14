#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' This cogs handles fun commands which has popculture references. '''

#-------------------------------------------------------------------------------

import os
import asyncio
import yaml
import discord
import typing
import random
import datetime
from pydub import AudioSegment
from pydub.generators import Sine
from discord.ext import commands
from discord.ext.commands import Context

tmp = "tmp"

class CosmicCon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.taunt = dict()
        self.taunt_gifs = ["https://tenor.com/view/willem-dafoe-laugh-crazy-car-gif-22580177",
                            "https://tenor.com/view/krillin-taunt-taunting-anime-dbz-gif-13298362",
                            "https://tenor.com/view/loafcat-meme-crypto-boxing-dance-gif-14735673580763849381"]


    ## Star Wars reference
    @commands.command(name='order66', description = "Exterminate all the Jedi from the Galactic Republic")
    @commands.has_permissions(administrator=True)
    async def order66(self, context: Context):
        ''' Ban all the users in the server'''
        # check if the user is the emperor (owner)
        if context.author.id != context.guild.owner_id:
            embed = discord.Embed(title="Order 66",
                                    description="Only the Emperor can execute Order 66",
                                    color=self.bot.default_color)
            await context.send(embed=embed)
            return
        # ask for confirmation
        embed = discord.Embed(title="Order 66",
                            description="Are you sure you want to execute **Order 66**?\nThis will ban all the users (Jedi) in the server (Galactic Republic).\n\nReact with ✅ to confirm.",
                                color=self.bot.default_color)
        message = await context.send(embed=embed)
        await message.add_reaction('✅')
        await message.add_reaction('❌')
        # wait for confirmation
        def check(reaction, user):
            return user == context.author and str(reaction.message.id) == str(message.id) and str(reaction.emoji) in ['✅', '❌']
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            embed = discord.Embed(title="Order 66",
                                description="Order 66 execution timed out",
                                color=self.bot.default_color)
            await message.edit(embed=embed)
            return
        # Abort Order 66
        if str(reaction.emoji) != '✅':
            embed = discord.Embed(title="Order 66",
                                description="Order 66 execution aborted",
                                color=self.bot.default_color)
            await message.edit(embed=embed)
            return
        # Execute Order 66
        embed = discord.Embed(title="Order 66",
                            description="It will be done, my Lord",
                            color=self.bot.default_color)
        await message.edit(embed=embed)
        for member in context.guild.members:
            # member not bot or not admin
            if not member.bot and not member.guild_permissions.administrator:
                await member.ban(reason="By the order of the Emperor")
        embed = discord.Embed(title="Order 66",
                            description="All the users (Jedi) have been banned",
                            color=self.bot.default_color)
        await context.send(embed=embed)
        self.bot.log.info(f"Order 66 executed by {context.author.name} in {context.guild.name}", context.guild)

    ## Thanos reference
    @commands.command(name='thanos_snap', description = "Eliminate half of the population from the known universe")
    @commands.has_permissions(administrator=True)
    async def snap(self, context: Context):
        ''' kick half of the users in the server '''
        # check if the user is the emperor (owner)
        if context.author.id != context.guild.owner_id:
            embed = discord.Embed(title="The Snap",
                                description="You need all the infinity stones to snap",
                                color=self.bot.default_color)
            await context.send(embed=embed)
            return
        # ask for confirmation
        embed = discord.Embed(title="The Snap :headstone:",
                            description="Are you sure you want to snap and ban half of the users in the server?\n\nReact with ✅ to confirm.",
                                color=self.bot.default_color)
        message = await context.send(embed=embed)
        await message.add_reaction('✅')
        await message.add_reaction('❌')
        def check(reaction, user):
            return user == context.author and str(reaction.message.id) == str(message.id) and str(reaction.emoji) in ['✅', '❌']
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            embed = discord.Embed(title="The Snap", 
                                description="The Snap execution timed out", 
                                color=self.bot.default_color)
            await message.edit(embed=embed)
            return
        # Abort Snap
        if str(reaction.emoji) != '✅':
            embed = discord.Embed(title="The Snap",
                                    description = "The Snap execution aborted",
                                    color=self.bot.default_color)
            await message.edit(embed=embed)
            return
        # Execute Snap
        embed = discord.Embed(title="The Snap",
                            description="I am inevitable",
                            color=self.bot.default_color)
        await message.edit(embed=embed)
        # Ban half of the users at random
        members = context.guild.members
        members = [member for member in members if not member.bot and not member.guild_permissions.administrator]
        for i, member in enumerate(members):
            if i % 2 == 0:
                await member.kick(reason=f"snapped by {context.author.name}")
        embed = discord.Embed(title="The Snap",
                            description="Perfectly balanced, as all things should be",
                            color=self.bot.default_color)
        await context.send(embed=embed)
        self.bot.log.info(f"The Snap executed by {context.author.name} in {context.guild.name}", context.guild)


    ## Harry Potter reference
    @commands.command(name='avada_kedavra', description = "Shutdown a muggle")
    @commands.has_permissions(administrator=True)
    async def avada_kedavra(self, context: Context, member: discord.Member):
        ''' disconnect a user from the voice channel '''
        if not context.author.guild_permissions.kick_members:
            embed = discord.Embed(title="Avada Kedavra",
                                description="You need to be a wizard to use this spell",
                                color=self.bot.default_color)
            await context.send(embed=embed)
            return
        if member.voice is not None:
            embed = discord.Embed(title="Avada Kedavra",
                                    description=f"{member.mention} is not in a voice channel",
                                    color=self.bot.default_color)
            await context.send(embed=embed)
            return
        await member.move_to(None)
        embed = discord.Embed(title="Avada Kedavra",
                                description=f"{member.mention} has been Sectumsempra'd",
                                color=self.bot.default_color) 
        await context.send(embed=embed)
        self.bot.log.info(f"Muggle {member.name} has been Avada Kedavra'd by {context.author.name} in {context.guild.name}", context.guild)

    @commands.command(name='wingardium_leviosa', aliases=['leviosa'], description = "throw a muggle away")
    async def wingardium_leviosa(self, context: Context, member: discord.Member):
        ''' Move a user to a different voice channel - 3 times with a delay '''
        if not context.author.guild_permissions.move_members:
            embed = discord.Embed(title="Wingardium Leviosa",
                                description="You need to practice more to use this spell",
                                color=self.bot.default_color)
            await context.send(embed=embed)
            return
        if member.voice is None:
            embed = discord.Embed(title="Wingardium Leviosa",
                                description=f"{member.mention} is not in a voice channel",
                                color=self.bot.default_color)
            await context.send(embed=embed)
            return
        original_channel = member.voice.channel
        voice_channels = context.guild.voice_channels
        voice_channels.remove(original_channel)
        voice_channels = random.sample(voice_channels, 3)
        for channel in voice_channels:
            await member.move_to(channel)
            await asyncio.sleep(3)
        await member.move_to(original_channel)
        embed = discord.Embed(title="Wingardium Leviosa",
                            description=f"{member.mention} has been thrown around",
                            color=self.bot.default_color)
        await context.send(embed=embed)
        self.bot.log.info(f"Muggle {member.name} has been Wingardium Leviosa'd by {context.author.name} in {context.guild.name}", context.guild)



    ## Naruto reference
    @commands.command(name='tsukuyomi', description = "Trap a shinobi in an illusion for 72 hours")
    async def tsukuyomi(self, context: Context, member: discord.Member):
        ''' Taunt a user for 72 hours wheneever they send a message '''
        if not context.author.guild_permissions.moderate_members:
            embed = discord.Embed(title="Tsukuyomi",
                                description="You need to be a chunin or higher to use this jutsu",
                                color=self.bot.default_color)
            await context.send(embed=embed)
            return
        self.taunt[member.id] = datetime.datetime.now(tz=datetime.timezone.utc)+datetime.timedelta(hours=72)
        embed = discord.Embed(title="Tsukuyomi",
                            description=f"{member.mention} has been trapped in the Tsukuyomi for next 72 hours",
                            color=self.bot.default_color)
        await context.send(embed=embed)
        self.bot.log.info(f"Shinobi {member.name} has been trapped in Tsukuyomi by {context.author.name} in {context.guild.name}", context.guild)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        ''' Check if the user is taunted '''
        if message.author.id in self.taunt:
            if datetime.datetime.now(tz=datetime.timezone.utc) < self.taunt[message.author.id]:
                gif = random.choice(self.taunt_gifs)
                await message.reply(f"{message.author.mention} {gif}")
            else:
                self.taunt.pop(message.author.id, None)

    ## R2D2 reference
    @commands.command(name='r2d2', description = "Translate a message to R2D2's language")
    async def r2d2(self, context: Context, *, message: str):
        ''' Translate the message to R2D2's language '''
        r2d2_message = [ f"{ord(char):08b}" for char in message]
        r2d2_message = ' '.join(r2d2_message)
        # Generate sound based on binary message
        beep = Sine(1000).to_audio_segment(duration=200)  # 1000Hz tone for '1'
        boop = Sine(500).to_audio_segment(duration=200)  # 500Hz tone for '0'
        final_audio = AudioSegment.silent(duration=0)
        for bit in r2d2_message:
            if bit == '1':
                final_audio += beep
            else:
                final_audio += boop
        audio_path = os.path.join(tmp, "translated.wav")
        final_audio.export(audio_path, format='wav')
        embed = discord.Embed(title="R2D2",
                                description="Beep Boop Beep!",
                                color=self.bot.default_color)
        await context.send(embed=embed)
        await context.send(file=discord.File(audio_path))
        os.remove(audio_path)
        self.bot.log.info(f"Message translated to R2D2's language by {context.author.name} in {context.guild.name}", context.guild)
        

async def setup(bot):
    await bot.add_cog(CosmicCon(bot))