#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Radio related commands for the bot '''

#-------------------------------------------------------------------------------

import os
import yaml
import gtts
import asyncio
import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands import Context

tmp = "tmp"

class Radio(commands.Cog, name="Radio FM"):
    def __init__(self, bot):
        self.bot = bot
        self.volume = 80
        self.called_channel = dict()
        self.now_playing = dict()

    @commands.command(name="play", aliases=["fm", "pl"], description="Play radio in the voice channel")
    async def radio(self, context: Context, radio_name: str):
        ''' Play radio in the voice channel '''
        radio_name = radio_name.lower()
        radio_list = self.get_radio_list(context.guild.id)
        if radio_name.isdigit():
            if int(radio_name) > len(radio_list) or int(radio_name) < 1:
                embed = discord.Embed(
                        title="Radio FM",
                        description="Invalid radio number",
                        color=self.bot.default_color,
                        )
                await context.reply(embed=embed)
                self.bot.log.warning(f"Invalid radio number", context.guild)
                return
            radio_name = list(radio_list.keys())[int(radio_name)-1]
        elif radio_name not in radio_list:
            embed = discord.Embed(
                    title="Radio FM",
                    description=f"Radio {radio_name} not found",
                    color=self.bot.default_color,
                    )
            await context.reply(embed=embed)
            self.bot.log.warning(f"Radio {radio_name} not found", context.guild)
            return
        radio_url = radio_list[radio_name]
        if context.voice_client is None:
            if not await self.join(context):
                return
        elif context.voice_client.is_playing():
            if self.now_playing.get(context.guild.id, None) is not None:
                if radio_name == self.now_playing[context.guild.id]:
                    embed = discord.Embed(
                            title="Radio FM",
                            description=f"Radio {radio_name} is already playing in {context.voice_client.channel.mention}",
                            color=self.bot.default_color,
                            )
                    await context.reply(embed=embed)
                    self.bot.log.warning(f"Radio {radio_name} is already playing in {context.voice_client.channel.name}", context.guild)
                    return
            context.voice_client.stop()
        # Say the radio name
        if self.now_playing.get(context.guild.id, None) is not None:
            now_playing = self.now_playing[context.guild.id]
            text = f"Switching from {now_playing.replace('_', ' ')} to {radio_name.replace('_', ' ')} radio station"
        else:
            text = f"Playing the radio station {radio_name.replace('_', ' ')}"
        tts = gtts.gTTS(text, lang="en", tld="com.au")
        file = os.path.join(tmp, "radio_welcome.mp3")
        os.makedirs(os.path.dirname(file), exist_ok=True)
        tts.save(file)
        context.voice_client.play(discord.FFmpegPCMAudio(file))
        context.voice_client.source = discord.PCMVolumeTransformer(context.voice_client.source)
        while context.voice_client.is_playing():
            await asyncio.sleep(1)
        os.remove(file)
        # Play the radio
        self.now_playing[context.guild.id] = radio_name
        context.voice_client.play(discord.FFmpegPCMAudio(radio_url))
        context.voice_client.source = discord.PCMVolumeTransformer(context.voice_client.source, volume=self.volume/100)
        embed = discord.Embed(
                title="Radio FM",
                description=f"{text} in {context.voice_client.channel.mention} :radio:",
                color=self.bot.default_color,
                )
        await context.reply(embed=embed)
        self.bot.log.info(f"Playing radio {radio_name} in {context.voice_client.channel.name}", context.guild)
        return

    @commands.command(name="stop", aliases=["s"], description="Stop radio in the voice channel")
    async def radio_stop(self, context: Context):
        ''' Stop radio in the voice channel '''
        voice_client = discord.utils.get(self.bot.voice_clients, guild=context.guild)
        if voice_client is None:
            embed = discord.Embed(
                    title="Radio FM",
                    description="I am not in a voice channel",
                    color=self.bot.default_color,
                    )
            await context.reply(embed=embed)
            self.bot.log.warning(f"Bot not in a voice channel", context.guild)
            return
        voice_client.stop()
        self.now_playing.pop(context.guild.id, None)
        await voice_client.disconnect()
        embed = discord.Embed(
                title="Radio FM",
                description="I have stopped the radio",
                color=self.bot.default_color,
                )
        await context.reply(embed=embed)
        self.bot.log.info(f"Stopped radio in {voice_client.channel.name}", context.guild)
        return

    @commands.command(name="list", aliases=["l"], description="List of available radio stations")
    async def radio_list(self, context: Context):
        ''' List of available radio stations '''
        radio_list = self.get_radio_list(context.guild.id)
        radio_list = "\n".join([f"{idx+1}. [{radio_name}]({radio_url})" for idx, (radio_name, radio_url) in enumerate(radio_list.items())])
        embed = discord.Embed(
                title="Radio FM",
                description=radio_list,
                color=self.bot.default_color,
                )
        await context.reply(embed=embed)
        return
    
    @commands.command(name="add", aliases=["a"], description="Add radio station to the list")
    async def radio_add(self, context: Context, radio_name: str, radio_url: str):
        ''' Add radio station to the list '''
        radio_list = self.get_radio_list(context.guild.id)
        radio_name = radio_name.lower()
        if radio_name in radio_list:
            embed = discord.Embed(
                    title="Radio FM",
                    description=f"Radio {radio_name} already exists",
                    color=self.bot.default_color,
                    )
            await context.reply(embed=embed)
            self.bot.log.warning(f"Radio {radio_name} already exists", context.guild)
            return
        is_streaming_url_valid = await self.check_streaming_url(radio_url)
        if not is_streaming_url_valid:
            embed = discord.Embed(
                    title="Radio FM",
                    description="Invalid streaming URL",
                    color=self.bot.default_color,
                    )
            await context.reply(embed=embed)
            self.bot.log.warning(f"Invalid streaming URL", context.guild)
            return
        radio_list[radio_name] = radio_url
        self.save_radio_list(context.guild.id, radio_list)
        embed = discord.Embed(
                title="Radio FM",
                description=f"Radio {radio_name} added successfully",
                color=self.bot.default_color,
                )
        await context.reply(embed=embed)
        self.bot.log.info(f"Added radio {radio_name} to the list", context.guild)
        return

    @commands.command(name="remove", aliases=["r"], description="Remove radio station from the list")
    async def radio_remove(self, context: Context, radio_name: str):
        ''' Remove radio station from the list '''
        radio_list = self.get_radio_list(context.guild.id)
        radio_name = radio_name.lower()
        if radio_name.isdigit():
            if int(radio_name) > len(radio_list) or int(radio_name) < 1:
                embed = discord.Embed(
                        title="Radio FM",
                        description="Invalid radio number",
                        color=self.bot.default_color,
                        )
                await context.reply(embed=embed)
                self.bot.log.warning(f"Invalid radio number", context.guild)
                return
            radio_name = list(radio_list.keys())[int(radio_name)-1]
        if radio_name not in radio_list:
            embed = discord.Embed(
                    title="Radio FM",
                    description=f"Radio {radio_name} not found",
                    color=self.bot.default_color,
                    )
            await context.reply(embed=embed)
            self.bot.log.warning(f"Radio {radio_name} not found", context.guild)
            return
        radio_list.pop(radio_name)
        self.save_radio_list(context.guild.id, radio_list)
        embed = discord.Embed(
                title="Radio FM",
                description=f"Radio {radio_name} removed successfully from the list",
                color=self.bot.default_color,
                )
        await context.reply(embed=embed)
        self.bot.log.info(f"Removed radio {radio_name} from the list", context.guild)

    @commands.command(name="rename", aliases=["rn"], description="Rename radio station in the list")
    async def radio_rename(self, context: Context, radio_name: str, new_name: str):
        ''' Rename radio station in the list '''
        radio_list = self.get_radio_list(context.guild.id)
        radio_name = radio_name.lower()
        new_name = new_name.lower()
        if radio_name.isdigit():
            if int(radio_name) > len(radio_list) or int(radio_name) < 1:
                embed = discord.Embed(
                        title="Radio FM",
                        description="Invalid radio number",
                        color=self.bot.default_color,
                        )
                await context.reply(embed=embed)
                self.bot.log.warning(f"Invalid radio number", context.guild)
                return
            radio_name = list(radio_list.keys())[int(radio_name)-1]
        if radio_name not in radio_list:
            embed = discord.Embed(
                    title="Radio FM",
                    description=f"Radio {radio_name} not found",
                    color=self.bot.default_color,
                    )
            await context.reply(embed=embed)
            self.bot.log.warning(f"Radio {radio_name} not found", context.guild)
            return
        if new_name in radio_list:
            embed = discord.Embed(
                    title="Radio FM",
                    description=f"Radio {new_name} already exists",
                    color=self.bot.default_color,
                    )
            await context.reply(embed=embed)
            self.bot.log.warning(f"Radio {new_name} already exists", context.guild)
            return
        radio_list[new_name] = radio_list.pop(radio_name)
        self.save_radio_list(context.guild.id, radio_list)
        embed = discord.Embed(
                title="Radio FM",
                description=f"Radio {radio_name} renamed to {new_name} successfully",
                color=self.bot.default_color,
                )
        await context.reply(embed=embed)
        self.bot.log.info(f"Renamed radio {radio_name} to {new_name}", context.guild)
    
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
            self.now_playing.pop(context.guild.id, None)
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
            if str(guild_id) in os.listdir(self.bot.data_dir):
                if os.path.exists(os.path.join(self.bot.data_dir, str(guild_id), "radio.yml")):
                    with open(os.path.join(self.bot.data_dir, str(guild_id), "radio.yml"), "r") as file:
                        radio_list = yaml.load(file, Loader=yaml.FullLoader)
                        return radio_list
        self.bot.log.warning(f"No radio list found for {str(guild_id)}")
        return dict()
    
    def save_radio_list(self, guild_id, radio_list):
        ''' Save radio list to the config file '''
        if os.path.exists(self.bot.data_dir):
            if not str(guild_id) in os.listdir(self.bot.data_dir):
                os.mkdir(os.path.join(self.bot.data_dir, str(guild_id)))
            with open(os.path.join(self.bot.data_dir, str(guild_id), "radio.yml"), "w+") as file:
                yaml.dump(radio_list, file)
        self.bot.log.info(f"Saved radio list for {str(guild_id)}")
        return
    
    async def check_streaming_url(self, radio_url: str):
        ''' Check if the streaming URL is valid '''
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(radio_url) as response:
                    # Check if the URL responds with a status code 200 (OK)
                    if response.status == 200:
                        # Check the Content-Type header to ensure it's an audio stream
                        content_type = response.headers.get('Content-Type', '').lower()
                        if 'audio' in content_type:
                            self.bot.log.info(f"Streaming URL {radio_url} is valid")
                            return True
        except Exception as e:
            self.bot.log.warning(f"Error checking streaming URL: {e}")
        self.bot.log.warning(f"Streaming URL {radio_url} is invalid")
        return False

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        ''' Disconnect bot when no one is in the voice channel '''
        if member == self.bot.user: return # ignore bot
        voice_client = member.guild.voice_client
        if voice_client is None: return
        if before.channel == voice_client.channel and (after.channel != voice_client.channel or after.channel is None):
            if len(before.channel.members) == 1:
                # Stop playing if the bot is playing something
                if voice_client.is_playing():
                    voice_client.stop()
                    self.now_playing.pop(before.channel.guild.id, None)
                await voice_client.disconnect()
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
