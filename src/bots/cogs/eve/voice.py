#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Voice features such as join and leave voice channel '''

#-------------------------------------------------------------------------------

import os
import regex
import shutil
import asyncio
import discord
from discord.ext import commands
from discord.ext.commands import Context
from .. import tts

MAX_SAY_LENGTH = 300
AUDIO_EXTENSIONS = (".mp3", ".ogg", ".wav", ".m4a")

class Voice(commands.Cog, name="Voice Features"):
    def __init__(self, bot):
        self.bot = bot
        self.volume = 90
        self.called_channel = dict()
        self.session_voices = dict()   # guild_id -> {user_id: index in tts.USER_VOICES}; cleared when EVE leaves voice
        self.greet_messages = dict()
        self.load_greet_messages()
        self.bot.log.info(f"Voice features initialized with volume {self.volume}")

    @commands.command(name="join", description="Join a voice channel (id or name); without one, joins the voice channel of the user", aliases=["j"])
    async def join(self, context: Context, voice_channel: discord.VoiceChannel = None):
        ''' Join the voice channel of the user '''
        if voice_channel is None:
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
        if context.guild.voice_client is not None:
            await self._hard_disconnect(context.guild, force=True)
        try:
            await voice_channel.connect()
        except Exception as e:
            self.bot.log.warning(f"Voice connect failed, retrying after hard reset: {e}", context.guild)
            await self._hard_disconnect(context.guild, force=True)
            await asyncio.sleep(1)
            await voice_channel.connect()

        embed = discord.Embed(
            title=f"Joined {voice_channel.name} :microphone:",
            description="I have joined the voice channel",
            color=self.bot.default_color,
        )
        await context.reply(embed=embed)
        self.bot.log.info(
            f"{self.bot.name} joined voice channel {voice_channel.name} in {context.guild.name}",
            context.guild,
        )
        return True
    
    @commands.command(name="say", description="Say the text in the bot's voice channel; if not in voice, joins the user's channel (use join <channel> first otherwise)", aliases=["s"])
    async def say(self, context: Context, *, text: str):
        ''' Say the text in the voice channel '''
        if getattr(context, "bridged", False):   # asked through GO-4 -> EVE's own voice
            voice_name, voice = "Pallavi", tts.EVE_VOICE
        else:
            voice_name, voice = self.session_voice(context.guild.id, context.author.id)
        await self.speak(context, text, voice, voice_name)

    def session_voice(self, guild_id, user_id):
        ''' Voice of a user for this voice session: 1st user gets voice 1, 2nd voice 2, ... wraps after 7 '''
        voices = self.session_voices.setdefault(guild_id, dict())
        if user_id not in voices:
            voices[user_id] = len(voices) % len(tts.USER_VOICES)
        return tts.USER_VOICES[voices[user_id]]

    async def speak(self, context: Context, text: str, voice: str, voice_name: str):
        ''' Clean the text, convert Tanglish, synthesize and play it in the voice channel '''
        if len(text) > MAX_SAY_LENGTH:
            embed = discord.Embed(
                title="Too long :scroll:",
                description=f"Please keep it under {MAX_SAY_LENGTH} characters",
                color=self.bot.default_color,
                )
            await context.reply(embed=embed)
            return
        if context.voice_client is None:
            if not await self.join(context):
                return
        if context.voice_client.is_playing():
            embed = discord.Embed(
                title="Already speaking :tired_face:",
                description="I am already speaking. Please wait for me to finish",
                color=self.bot.default_color,
                )
            await context.reply(embed=embed)
            self.bot.log.warning(f"{context.author} tried to use say command when already speaking in voice channel {context.voice_client.channel.name} in {context.guild.name}", context.guild)
            # wait for the bot to finish speaking
            while context.voice_client is not None and context.voice_client.is_playing():
                await asyncio.sleep(1)
            if context.voice_client is None:
                return
        # Replace mentions with their display names
        for mention in context.message.mentions:
            text = text.replace(mention.mention, mention.display_name)
        for role in context.message.role_mentions:
            text = text.replace(role.mention, role.name)
        for channel in context.message.channel_mentions:
            text = text.replace(channel.mention, channel.name)
        # Replace repeated emojis with a single instance
        text = regex.sub(r'(\p{Emoji_Presentation})(\1+)', r'\1', text)
        # Replace server emojis with their names
        for emoji in context.message.guild.emojis:
            text = text.replace(str(emoji), emoji.name)
        spoken = await tts.to_tamil_script(text)
        try:
            file = await tts.synthesize(spoken, voice)
        except Exception as e:
            embed = discord.Embed(
                title="Voice service is down :mute:",
                description="I couldn't generate the voice right now. Please try again later",
                color=self.bot.default_color,
                )
            await context.reply(embed=embed)
            self.bot.log.error(f"edge-tts failed for voice {voice}: {e}", context.guild)
            return
        if context.voice_client is None:
            tts.remove_file(file)
            return
        context.voice_client.play(discord.FFmpegPCMAudio(file), after=lambda error: tts.remove_file(file))
        context.voice_client.source = discord.PCMVolumeTransformer(context.voice_client.source)
        context.voice_client.source.volume = self.volume / 100
        embed = discord.Embed(
            title="Speaking :speaking_head:",
            description=" *'" + text + "'*\n\n:loud_sound: " + context.voice_client.channel.mention,
            color=self.bot.default_color,
            )
        embed.set_footer(text=f"Voice: {voice_name}")
        await context.reply(embed=embed)
        self.bot.log.info(f"{context.author} used say with voice {voice_name}: '{text}' (spoken: '{spoken}') in voice channel {context.voice_client.channel.name} in {context.guild.name}", context.guild)

    @commands.command(name="leave", description="Leave the voice channel", aliases=["l"])
    async def leave(self, context: Context, force: bool = False):
        ''' Leave the voice channel '''
        if context.voice_client is None:
            embed = discord.Embed(
                title="Not in a voice channel :confused:",
                description="I am not in any voice channel. How can I leave?",
                color=self.bot.default_color,
                )
            await context.reply(embed=embed)
            self.bot.log.warning(f"{context.author} tried to use leave command without being in a voice channel", context.guild)
            return
        channel = context.voice_client.channel
        await self._hard_disconnect(context.guild, force=force)
        embed = discord.Embed(
            title="Left the voice channel :wave:",
            description="I have left the voice channel",
            color=self.bot.default_color,
            )
        await context.reply(embed=embed)
        self.bot.log.info(f"{self.bot.name} left voice channel {channel.name} in {context.guild.name}", context.guild)
    
    @commands.command(name="greet", description="Get or set the greet message for the user", aliases=["g"])
    async def greet(self, context: Context, member: discord.Member, *, text: str = None):
        ''' Get or set the greet message for the user '''
        if text is None:
            if str(context.guild.id) not in self.greet_messages.keys() or str(member.id) not in self.greet_messages.get(str(context.guild.id), dict()).keys():
                embed = discord.Embed(
                    title="No greet message :confused:",
                    description=f"No greet message set for {member.mention}",
                    color=self.bot.default_color,
                    )
                await context.reply(embed=embed)
                self.bot.log.info(f"No greet message set for {member.display_name} checked by {context.author} in {context.guild.name}", context.guild)
            else:
                embed = discord.Embed(
                    title="Greet message :wave:",
                    description=f"Greet message for {member.mention} is \n'{self.greet_messages[str(context.guild.id)][str(member.id)]}'",
                    color=self.bot.default_color,
                    )
                await context.reply(embed=embed)
                self.bot.log.info(f"Greet message for {member.display_name} is '{self.greet_messages[str(context.guild.id)][str(member.id)]}' checked by {context.author} in {context.guild.name}", context.guild)
        else:
            if str(context.guild.id) not in self.greet_messages.keys():
                self.greet_messages[str(context.guild.id)] = dict()
            self.greet_messages[str(context.guild.id)][str(member.id)] = text
            embed = discord.Embed(
                title="Greet message set :wave:",
                description=f"Greet message for {member.mention} is set to '{text}'",
                color=self.bot.default_color,
                )
            await context.reply(embed=embed)
            self.save_greet_messages()
            self.bot.log.info(f"{context.author} set the greet message for {member.display_name} to '{text}' in {context.guild.name}", context.guild)

    @commands.command(name="volume", description="Get or set the volume of the bot", aliases=["v"])
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
            embed = discord.Embed(
                title="Volume set :loud_sound:",
                description=f"Volume set to {self.volume}",
                color=self.bot.default_color,
                )
            await context.reply(embed=embed)
            self.bot.log.info(f"{context.author} set the volume to {volume} in {context.guild.name}", context.guild)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot: return
        voice_client = member.guild.voice_client
        if voice_client is None or voice_client.is_playing(): return # ignore if bot is not in a voice channel or is speaking
        if before.channel != after.channel and after.channel == voice_client.channel:
            name = member.display_name.replace('_', ' ').replace('.', ' ').strip()
            greet = str(self.greet_messages.get(str(member.guild.id), dict()).get(str(member.id), "") or "").strip()
            clip = None
            if greet.lower().endswith(AUDIO_EXTENSIONS):
                # greet is an audio file in data/<bot>/guilds/<id>/greet_audio/ (not in git) -> play only the clip
                clip = self.bot.guild_path(member.guild.id, "greet_audio", os.path.basename(greet))
                if not os.path.exists(clip):
                    self.bot.log.warning(f"Greet audio {greet} for {member.display_name} not found, using default greet", member.guild)
                    clip, greet = None, ""
            if clip is not None:
                file = os.path.join(tts.tmp, f"greet_{member.id}_{os.getpid()}{os.path.splitext(clip)[1]}")
                os.makedirs(tts.tmp, exist_ok=True)
                shutil.copyfile(clip, file)
            else:
                # text greet (Tanglish converted) or default Vanakkam; the name stays in English
                text = (await tts.to_tamil_script(greet)) if greet else "வணக்கம்"
                try:
                    file = await tts.synthesize(f"{text} {name}", tts.EVE_VOICE)
                except Exception as e:
                    self.bot.log.error(f"edge-tts failed for greet: {e}", member.guild)
                    return
            await asyncio.sleep(3)
            voice_client = member.guild.voice_client
            if voice_client is None or voice_client.is_playing():
                tts.remove_file(file)
                return
            voice_client.play(discord.FFmpegPCMAudio(file), after=lambda error: tts.remove_file(file))
            voice_client.source = discord.PCMVolumeTransformer(voice_client.source)
            voice_client.source.volume = self.volume / 100
            self.bot.log.info(f"{self.bot.name} greeted {member.display_name} in voice channel {voice_client.channel.name} in {member.guild.name}", member.guild)
        elif before.channel != after.channel and before.channel == voice_client.channel:
            if len(before.channel.members) == 1:
                await asyncio.sleep(5)
                voice_client_2 = before.channel.guild.voice_client
                if len(before.channel.members) == 1:
                    if voice_client_2.is_playing():
                        voice_client_2.stop()
                    await self._hard_disconnect(before.channel.guild, force=True)
                    embed = discord.Embed(
                        title="I'm leaving :wave:",
                        description=f"I have left the voice channel {before.channel.name} as I was alone",
                        color=self.bot.default_color,
                        )
                    called_channel = self.called_channel.get(before.channel.guild.id, None)
                    if called_channel is not None:
                        await called_channel.send(embed=embed)
                    self.bot.log.info(f"{self.bot.name} left voice channel {before.channel.name} in {before.channel.guild.name} as the last member left", before.channel.guild)

    async def _hard_disconnect(self, guild: discord.Guild, *, force: bool = True):
        ''' Forcefully disconnect the bot from the voice channel in the guild '''
        self.session_voices.pop(guild.id, None)
        voice_client = guild.voice_client
        if voice_client is None:
            return
        try:
            if voice_client.is_playing():
                voice_client.stop()
        except Exception:
            pass
        try:
            await voice_client.disconnect(force=force)
        except Exception:
            pass
    
    def save_greet_messages(self):
        ''' Save the greet messages to a file '''
        for guild_id, greet_set in self.greet_messages.items():
            self.bot.save_guild_yaml(guild_id, "greet_messages.yml", greet_set)
            self.bot.log.info(f"Greet messages saved")

    def load_greet_messages(self):
        ''' Load the greet messages from a file '''
        for guild_id in self.bot.list_guild_ids():
            guild_id = str(guild_id)
            greet_set = self.bot.load_guild_yaml(guild_id, "greet_messages.yml", default=None)
            if greet_set is not None:
                self.greet_messages[guild_id] = greet_set
        self.bot.log.info(f"Greet messages loaded")


async def setup(bot):
    await bot.add_cog(Voice(bot))