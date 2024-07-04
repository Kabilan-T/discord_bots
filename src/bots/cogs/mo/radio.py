#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Radio related commands for the bot '''

#-------------------------------------------------------------------------------

import os
import re
import yaml
import asyncio
import discord
from discord.ext import commands
from discord.ext.commands import Context

class Radio(commands.Cog, name="Radio FM"):
    def __init__(self, bot):
        self.bot = bot
        self.volume = 80

    @commands.command(name="play", aliases=["fm", "p"], help="Play radio in the voice channel")
    async def radio(self, context: Context, radio_name: str):
        ''' Play radio in the voice channel '''
        radio_name = radio_name.lower()
        radio_list = self.get_radio_list(context.guild.id)
        if radio_name not in radio_list:
            embed = discord.Embed(
                    title="Radio FM",
                    description=f"Radio {radio_name} not found",
                    color=self.bot.default_color,
                    )
            await context.send(embed=embed)
            self.bot.log.warning(f"Radio {radio_name} not found", context.guild)
            return
        elif radio_name.isdigit():
            if int(radio_name) > len(radio_list) or int(radio_name) < 1:
                embed = discord.Embed(
                        title="Radio FM",
                        description="Invalid radio number",
                        color=self.bot.default_color,
                        )
                await context.send(embed=embed)
                self.bot.log.warning(f"Invalid radio number", context.guild)
                return
            radio_name = list(radio_list.keys())[int(radio_name)-1]
        radio_url = radio_list[radio_name]
        if context.voice_client is None:
            if not await self.join(context):
                return
        elif context.voice_client.is_playing():
            context.voice_client.stop()
        context.voice_client.play(discord.FFmpegPCMAudio(radio_url))
        context.voice_client.source = discord.PCMVolumeTransformer(context.voice_client.source, volume=self.volume/100)
        embed = discord.Embed(
                title="Radio FM",
                description=f"Playing {radio_name} in {context.voice_client.channel.mention}",
                color=self.bot.default_color,
                )
        await context.send(embed=embed)
        self.bot.log.info(f"Playing radio {radio_name} in {context.voice_client.channel.name}", context.guild)
        while context.voice_client.is_playing():
            await asyncio.sleep(1)
        await context.voice_client.disconnect()
        return

    @commands.command(name="stop", aliases=["s"], help="Stop radio in the voice channel")
    async def radio_stop(self, context: Context):
        ''' Stop radio in the voice channel '''
        voice_client = discord.utils.get(self.bot.voice_clients, guild=context.guild)
        if voice_client is None:
            embed = discord.Embed(
                    title="Radio FM",
                    description="I am not in a voice channel",
                    color=self.bot.default_color,
                    )
            await context.send(embed=embed)
            self.bot.log.warning(f"Bot not in a voice channel", context.guild)
            return
        voice_client.stop()
        await voice_client.disconnect()
        embed = discord.Embed(
                title="Radio FM",
                description="I have stopped the radio",
                color=self.bot.default_color,
                )
        await context.send(embed=embed)
        self.bot.log.info(f"Stopped radio in {voice_client.channel.name}", context.guild)
        return

    @commands.command(name="list", aliases=["l"], help="List of available radio stations")
    async def radio_list(self, context: Context):
        ''' List of available radio stations '''
        radio_list = self.get_radio_list(context.guild.id)
        radio_list = "\n".join([f"{idx+1}. {radio_name}" for idx, radio_name in enumerate(radio_list.keys())])
        embed = discord.Embed(
                title="Radio FM",
                description=radio_list,
                color=self.bot.default_color,
                )
        await context.send(embed=embed)
        return
    
    @commands.command(name="add", aliases=["a"], help="Add radio station to the list")
    async def radio_add(self, context: Context, radio_name: str, radio_url: str):
        ''' Add radio station to the list '''
        radio_list = self.get_radio_list(context.guild.id)
        radio_name = radio_name.lower()
        radio_list[radio_name] = radio_url
        self.save_radio_list(context.guild.id, radio_list)
        embed = discord.Embed(
                title="Radio FM",
                description=f"Radio {radio_name} added successfully",
                color=self.bot.default_color,
                )
        await context.send(embed=embed)
        self.bot.log.info(f"Added radio {radio_name} to the list", context.guild)
        return
    
    @commands.command(name="join", aliases=["j"], description="Join the voice channel of the user")
    async def join(self, context: Context):
        ''' Join the voice channel of the user '''
        if context.author.voice is None:
            embed = discord.Embed(
                title="You are not in a voice channel :confused:",
                description="Please join a voice channel and try again",
                color=self.bot.default_color,
                )
            await context.reply(embed=embed)
            self.bot.log.warning(f"{context.author} tried to use join command without being in a voice channel", context.guild)
            return False
        voice_channel = context.author.voice.channel
        self.called_channel[context.guild.id] = context.channel
        if context.voice_client is None:
            await voice_channel.connect()
            embed = discord.Embed(
                title=f"Joined {voice_channel.name} :microphone:",
                description="I have joined the voice channel",
                color=self.bot.default_color,
                )
            await context.reply(embed=embed)
            self.bot.log.info(f"{self.bot.name} joined voice channel {voice_channel.name} in {context.guild.name}", context.guild)
            return True
        elif context.voice_client.channel == voice_channel:
            embed = discord.Embed(
                title=f"Already in {voice_channel.name} :confused:",
                description="I am already in the voice channel",
                color=self.bot.default_color,
                )
            await context.reply(embed=embed)
            self.bot.log.warning(f"{self.bot.name} tried to join voice channel {voice_channel.name} in {context.guild.name} when already in it", context.guild)
            return False
        else:
            await context.voice_client.move_to(voice_channel)
            embed = discord.Embed(
                title=f"Moved to {voice_channel.name} :person_running:",
                description="I have moved to the voice channel",
                color=self.bot.default_color,
                )
            await context.reply(embed=embed)
            self.bot.log.info(f"{self.bot.name} moved to voice channel {voice_channel.name} in {context.guild.name}", context.guild)
            return True
        

    @commands.command(name="volume", aliases=["v"], description="Get or set the volume of the bot")
    async def volume(self, context: Context, volume: int = None):
        ''' Get or set the volume of the bot '''
        if volume is None:
            embed = discord.Embed(
                title="Volume :loud_sound:",
                description=f"Volume is {self.volume}",
                color=self.bot.default_color,
                )
            await context.reply(embed=embed)
            self.bot.log.info(f"Current volume is {self.volume} checked by {context.author} in {context.guild.name}", context.guild)
        elif volume < 0 or volume > 100:
            embed = discord.Embed(
                title="Invalid volume :confused:",
                description="Please enter a volume between 0 and 100",
                color=self.bot.default_color,
                )
            await context.reply(embed=embed)
            self.bot.log.warning(f"{context.author} tried to set the volume to invalid volume {volume} in {context.guild.name}", context.guild)
        else:
            self.volume = volume
            if context.voice_client is not None:
                context.voice_client.source.volume = volume/100


            embed = discord.Embed(
                title="Volume set :loud_sound:",
                description=f"Volume set to {self.volume}",
                color=self.bot.default_color,
                )
            await context.reply(embed=embed)
            self.bot.log.info(f"{context.author} set the volume to {volume} in {context.guild.name}", context.guild)
        
    def get_radio_list(self, guild_id):
        ''' Get radio list from the config file '''
        if os.path.exists(self.bot.data_dir):
            if guild_id in os.listdir(self.bot.data_dir):
                if os.path.exists(os.path.join(self.bot.data_dir, guild_id, "radio.yml")):
                    with open(os.path.join(self.bot.data_dir, guild_id, "radio.yml"), "r") as file:
                        radio_list = yaml.load(file, Loader=yaml.FullLoader)
                        return radio_list
        self.bot.log.warning(f"No radio list found for {guild_id}")
        return dict()
    
    def save_radio_list(self, guild_id, radio_list):
        ''' Save radio list to the config file '''
        if os.path.exists(self.bot.data_dir):
            if not guild_id in os.listdir(self.bot.data_dir):
                os.mkdir(os.path.join(self.bot.data_dir, guild_id))
            with open(os.path.join(self.bot.data_dir, guild_id, "radio.yml"), "w+") as file:
                yaml.dump(radio_list, file)
        self.bot.log.info(f"Saved radio list for {guild_id}")
        return
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        ''' Disconnect bot when no one is in the voice channel '''
        if before.channel != after.channel and before.channel == member.guild.voice_client.channel:
            if len(before.channel.members) == 1:
                await before.channel.guild.voice_client.disconnect()
                embed = discord.Embed(
                    title="Radio FM",
                    description="I have disconnected as no one is in the voice channel",
                    color=self.bot.default_color,
                    )
                called_channel = self.called_channel.get(before.channel.guild.id,None)
                if called_channel is not None:
                    await called_channel.send(embed=embed)
                self.bot.log.info(f"Disconnected from voice channel {before.channel.name} in {before.channel.guild.name}")
    
async def setup(bot):
    await bot.add_cog(Radio(bot))
