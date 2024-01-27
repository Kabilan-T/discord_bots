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
        self.domain = self.bot.voice["domain"]
        self.available_languages = gtts.lang.tts_langs()
        try:
            response = requests.get("https://www.google.com/supported_domains").text.splitlines()
            self.available_domains = [domain.removeprefix(".google.") for domain in response]
        except:
            self.available_domains = [self.domain]
        self.bot.greet_messages = {}
        self.bot.logger.info(f"Voice features initialized with volume {self.volume}, language {self.language} and domain {self.domain}")

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
            return False
        voice_channel = context.author.voice.channel
        self.called_channel_id = context.channel.id
        if context.voice_client is None:
            await voice_channel.connect()
            embed = discord.Embed(title=f"Joined {voice_channel.name} :microphone:",
                                  description="I have joined the voice channel",
                                  color=0xBEBEFE,
                                  )
            await context.reply(embed=embed)
            self.bot.logger.info(f"{self.bot.name} joined voice channel {voice_channel.name} in {context.guild.name}")
            return True
        elif context.voice_client.channel == voice_channel:
            embed = discord.Embed(title=f"Already in {voice_channel.name} :confused:",
                                  description="I am already in the voice channel",
                                  color=0xBEBEFE,
                                  )
            await context.reply(embed=embed)
            self.bot.logger.info(f"{self.bot.name} tried to join voice channel {voice_channel.name} in {context.guild.name} when already in it")
            return False
        else:
            await context.voice_client.move_to(voice_channel)
            embed = discord.Embed(title=f"Moved to {voice_channel.name} :person_running:",
                                  description="I have moved to the voice channel",
                                  color=0xBEBEFE,
                                  )
            await context.reply(embed=embed)
            self.bot.logger.info(f"{self.bot.name} moved to voice channel {voice_channel.name} in {context.guild.name}")
            return True

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

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):        
        ''' Leave the voice channel when the last member leaves '''
        if member == self.bot.user: return # ignore bot
        if before.channel is not None and after.channel is None:
            if len(before.channel.members) == 1:
                await asyncio.sleep(5)
                if len(before.channel.members) == 1:
                    await before.channel.guild.voice_client.disconnect()
                    embed = discord.Embed(title="I'm leaving :wave:",
                                          description="I have left the voice channel as the last member left",
                                          color=0xBEBEFE,
                                          )
                    await self.bot.get_channel(self.called_channel_id).send(embed=embed)
                    self.bot.logger.info(f"{self.bot.name} left voice channel {before.channel.name} in {before.channel.guild.name} as the last member left")

    @commands.command(name="say", aliases=["s"])
    async def say(self, context: Context, *, text: str):
        ''' Say the text in the voice channel '''
        if context.voice_client is None:
            if not await self.join(context):
                return
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
        tts = gtts.gTTS(text, lang=self.language, tld=self.domain)
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
            self.bot.logger.info(f"{context.author} tried to use setvolume command with invalid volume {volume} in {context.guild.name}")
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
        if language not in self.available_languages.keys():
            embed = discord.Embed(title="Invalid language :confused:",
                                  description="Please enter a valid language.The available languages are:\n" + ",\t".join([f"'{key} - {value}'" for key, value in self.available_languages.items()]),
                                  color=0xBEBEFE,
                                  )
            await context.reply(embed=embed)
            self.bot.logger.info(f"{context.author} tried to use setlanguage command with invalid language {language} in {context.guild.name}")
            return
        self.language = language
        embed = discord.Embed(title="Language set :globe_with_meridians:",
                              description=f"Language set to '{language} - {self.available_languages[language]}'",
                              color=0xBEBEFE,
                              )
        await context.reply(embed=embed)
        self.bot.logger.info(f"{context.author} set the language to {language} in {context.guild.name}")

    @commands.command(name="setdomain", aliases=["sd"])
    async def setdomain(self, context: Context, domain: str):
        ''' Set the domain of the google text to speech '''
        if domain not in self.available_domains:
            embed = discord.Embed(title="Invalid domain :confused:",
                                  description="Please enter a valid domain.The available domains are:\n" + ",\t".join([f"'{domain}'" for domain in self.available_domains]),
                                  color=0xBEBEFE,
                                  )
            await context.reply(embed=embed)
            self.bot.logger.info(f"{context.author} tried to use setdomain command with invalid domain {domain} in {context.guild.name}")
            return
        self.domain = domain
        embed = discord.Embed(title="Domain set :globe_with_meridians:",
                              description=f"domain set to '{domain} - google.{domain}'",
                              color=0xBEBEFE,
                              )
        await context.reply(embed=embed)
        self.bot.logger.info(f"{context.author} set the domain to {domain} in {context.guild.name}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member == self.bot.user: return # ignore bot
        if before.channel is None and after.channel is not None:
            if after.channel == member.guild.voice_client.channel:
                await self.greet(member)
    
    async def greet(self, member):
        ''' Greet the member in the voice channel '''
        if member == self.bot.user: return
        if member.guild.voice_client is None:
            return
        if member.guild.voice_client.is_playing():
            return
        if member.guild.voice_client.channel != member.voice.channel:
            return
        if member.id in self.bot.greet_messages.keys():
            greet_message = self.bot.greet_messages[member.id] + f" {member.display_name}"
        else:
            greet_message = "Vanakkam " + f"{member.display_name}"
        tts = gtts.gTTS(f"{greet_message}", lang='ta', tld='co.in')
        file = os.path.join(temp_audio_dir, "greet.mp3")
        os.makedirs(os.path.dirname(file), exist_ok=True)
        tts.save(file)
        await asyncio.sleep(3)
        member.guild.voice_client.play(discord.FFmpegPCMAudio(file), after=lambda e: print("done", e))
        member.guild.voice_client.source = discord.PCMVolumeTransformer(member.guild.voice_client.source)
        member.guild.voice_client.source.volume = self.volume / 100
        self.bot.logger.info(f"{self.bot.name} greeted {member.display_name} in voice channel {member.guild.voice_client.channel.name} in {member.guild.name}")

    @commands.command(name="setgreet", aliases=["sg"])
    async def setgreet(self, context: Context, member: discord.Member, *, text: str):
        ''' Set the greet message for the user '''
        self.bot.greet_messages[member.id] = text
        embed = discord.Embed(title="Greet message set :wave:",
                              description=f"Greet message set to '{text}'",
                              color=0xBEBEFE,
                              )
        await context.reply(embed=embed)
        self.bot.logger.info(f"{context.author} set the greet message to {text} in {context.guild.name}")

async def setup(bot):
    await bot.add_cog(Voice(bot))


