#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Voice features such as join and leave voice channel '''

#-------------------------------------------------------------------------------

import os
import gtts
import asyncio
import requests
import discord
from discord.ext import commands
from discord.ext.commands import Context

temp_audio_dir = "generated_audio"

class Voice(commands.Cog, name="Voice Features"):
    def __init__(self, bot):
        self.bot = bot
        self.volume = self.bot.voice["default_volume"]
        self.language = self.bot.voice["language"]
        self.accent = self.bot.voice["accent"]
        self.available_languages = gtts.lang.tts_langs().keys()
        try:
            response = requests.get("https://www.google.com/supported_domains").text.splitlines()
            self.available_accents = [domain.removeprefix(".google.") for domain in response]
        except:
            self.available_accents = [self.accent]

    @commands.command(name="join", aliases=["j"])
    async def join(self, context: Context):
        ''' Join the voice channel of the user '''
        if context.author.voice is None:
            embed = discord.Embed(title="You are not in a voice channel :confused:",
                                  description="Please join a voice channel and try again",
                                  color=0xBEBEFE,
                                  )
            await context.reply(embed=embed)
            self.bot.logger.info(f"{context.author} tried to use join command without being in a voice channel")
            return
        voice_channel = context.author.voice.channel
        if context.voice_client is None:
            await voice_channel.connect()
            embed = discord.Embed(title=f"Joined {voice_channel.name} :microphone:",
                                  description="I have joined the voice channel",
                                  color=0xBEBEFE,
                                  )
            await context.reply(embed=embed)
            self.bot.logger.info(f"{self.bot.name} joined voice channel {voice_channel.name} in {context.guild.name}")
        elif context.voice_client.channel == voice_channel:
            embed = discord.Embed(title=f"Already in {voice_channel.name} :confused:",
                                  description="I am already in the voice channel",
                                  color=0xBEBEFE,
                                  )
            await context.reply(embed=embed)
            self.bot.logger.info(f"{self.bot.name} tried to join voice channel {voice_channel.name} in {context.guild.name} when already in it")
        else:
            await context.voice_client.move_to(voice_channel)
            embed = discord.Embed(title=f"Moved to {voice_channel.name} :person_running:",
                                  description="I have moved to the voice channel",
                                  color=0xBEBEFE,
                                  )
            await context.reply(embed=embed)
            self.bot.logger.info(f"{self.bot.name} moved to voice channel {voice_channel.name} in {context.guild.name}")

    @commands.command(name="leave", aliases=["l"])
    async def leave(self, context: Context):
        ''' Leave the voice channel '''
        if context.voice_client is None:
            embed = discord.Embed(title="Not in a voice channel :confused:",
                                  description="I am not in any voice channel. How can I leave?",
                                  color=0xBEBEFE,
                                  )
            await context.reply(embed=embed)
            self.bot.logger.info(f"{context.author} tried to use leave command without being in a voice channel")
            return
        channel = context.voice_client.channel
        await context.voice_client.disconnect()
        embed = discord.Embed(title="Left the voice channel :wave:",
                              description="I have left the voice channel",
                              color=0xBEBEFE,
                              )
        await context.reply(embed=embed)
        self.bot.logger.info(f"{self.bot.name} left voice channel {channel.name} in {context.guild.name}")

    @commands.command(name="say", aliases=["s"])
    async def say(self, context: Context, *, text: str):
        ''' Say the text in the voice channel '''
        if context.voice_client is None:
            await self.join(context)
        if context.voice_client.is_playing():
            embed = discord.Embed(title="Already speaking :tired_face:",
                                  description="I am already speaking. Please wait for me to finish",
                                  color=0xBEBEFE,
                                  )
            await context.reply(embed=embed)
            self.bot.logger.info(f"{context.author} tried to use say command when already speaking in voice channel {context.voice_client.channel.name} in {context.guild.name}")
            # wait for the bot to finish speaking
            while context.voice_client.is_playing():
                await asyncio.sleep(1)
        tts = gtts.gTTS(text, lang=self.language, tld=self.accent)
        file = os.path.join(temp_audio_dir, "tts.mp3")
        os.makedirs(os.path.dirname(file), exist_ok=True)
        tts.save(file)
        context.voice_client.play(discord.FFmpegPCMAudio(file), after=lambda e: print("done", e))
        context.voice_client.source = discord.PCMVolumeTransformer(context.voice_client.source)
        context.voice_client.source.volume = self.volume / 100
        embed = discord.Embed(title="Speaking :speaking_head:",
                              description=" *'" + text + "'*",
                              color=0xBEBEFE,
                              )
        await context.reply(embed=embed)
        self.bot.logger.info(f"{context.author} used say the text '{text}' in voice channel {context.voice_client.channel.name} in {context.guild.name}")

    @commands.command(name="volume", aliases=["v"])
    async def volume(self, context: Context):
        ''' Get the volume of the bot '''
        embed = discord.Embed(title="Volume :loud_sound:",
                              description=f"Volume is {self.volume}",
                              color=0xBEBEFE,
                              )
        await context.reply(embed=embed)
        self.bot.logger.info(f"Current volume is {self.volume} checked by {context.author} in guild {context.guild.name}")

    @commands.command(name="setvolume", aliases=["sv"])
    async def setvolume(self, context: Context, volume: int):
        ''' Set the volume of the bot '''
        if volume < 0 or volume > 100:
            embed = discord.Embed(title="Invalid volume :confused:",
                                  description="Please enter a volume between 0 and 100",
                                  color=0xBEBEFE,
                                  )
            await context.reply(embed=embed)
            self.bot.logger.info(f"{context.author} tried to use setvolume command with invalid volume {volume} in voice channel {context.voice_client.channel.name} in {context.guild.name}")
            return
        self.volume = volume
        embed = discord.Embed(title="Volume set :loud_sound:",
                              description=f"Volume set to {self.volume}",
                              color=0xBEBEFE,
                              )
        await context.reply(embed=embed)
        self.bot.logger.info(f"{context.author} set the volume to {volume} in {context.guild.name}")

    @commands.command(name="setlanguage", aliases=["sl"])
    async def setlanguage(self, context: Context, language: str):
        ''' Set the language of the bot '''
        if language not in self.available_languages:
            embed = discord.Embed(title="Invalid language :confused:",
                                  description="Please enter a valid language.The available languages are:\n" + "\n".join(self.available_languages),
                                  color=0xBEBEFE,
                                  )
            await context.reply(embed=embed)
            self.bot.logger.info(f"{context.author} tried to use setlanguage command with invalid language {language} in voice channel {context.voice_client.channel.name} in {context.guild.name}")
            return
        self.language = language
        embed = discord.Embed(title="Language set :globe_with_meridians:",
                              description=f"Language set to {self.language}",
                              color=0xBEBEFE,
                              )
        await context.reply(embed=embed)
        self.bot.logger.info(f"{context.author} set the language to {language} in {context.guild.name}")

    @commands.command(name="setaccent", aliases=["sa"])
    async def setaccent(self, context: Context, accent: str):
        ''' Set the accent of the bot '''
        if accent not in gtts.lang.tts_langs().keys():
            embed = discord.Embed(title="Invalid accent :confused:",
                                  description="Please enter a valid accent.The available accents are:\n" + "\n".join(self.available_accents),
                                  color=0xBEBEFE,
                                  )
            await context.reply(embed=embed)
            self.bot.logger.info(f"{context.author} tried to use setaccent command with invalid accent {accent} in voice channel {context.voice_client.channel.name} in {context.guild.name}")
            return
        self.accent = accent
        embed = discord.Embed(title="Accent set :globe_with_meridians:",
                              description=f"Accent set to {self.accent}",
                              color=0xBEBEFE,
                              )
        await context.reply(embed=embed)
        self.bot.logger.info(f"{context.author} set the accent to {accent} in {context.guild.name}")

async def setup(bot):
    await bot.add_cog(Voice(bot))


