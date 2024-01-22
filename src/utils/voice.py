#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Voice features such as join and leave voice channel '''

#-------------------------------------------------------------------------------

import discord
from discord.ext import commands
from discord.ext.commands import Context

class Voice(commands.Cog, name="Voice Features"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="join", aliases=["j"])
    async def join(self, context: Context):
        ''' Join the voice channel of the user '''
        if context.author.voice is None:
            await context.send("You are not in a voice channel")
            return
        voice_channel = context.author.voice.channel
        if context.voice_client is None:
            await voice_channel.connect()
            await context.send(f"Joined {voice_channel.name}")
        else:
            await context.voice_client.move_to(voice_channel)
            await context.send(f"Moved to {voice_channel.name}")

    @commands.command(name="leave", aliases=["l"])
    async def leave(self, context: Context):
        ''' Leave the voice channel '''
        if context.voice_client is None:
            await context.send("I am not in a voice channel")
            return
        await context.voice_client.disconnect()
        await context.send("Disconnected")

    @commands.command(name="play", aliases=["p"])
    async def play(self, context: Context, url: str):
        ''' Play audio from a youtube url '''
        if context.voice_client is None:
            await context.send("I am not in a voice channel")
            return
        if not context.voice_client.is_playing():
            context.voice_client.play(discord.FFmpegPCMAudio(url))
            await context.send("Playing")
        else:
            await context.send("Already playing")

    @commands.command(name="pause")
    async def pause(self, context: Context):
        ''' Pause the audio '''
        if context.voice_client is None:
            await context.send("I am not in a voice channel")
            return
        if context.voice_client.is_playing():
            context.voice_client.pause()
            await context.send("Paused")
        else:
            await context.send("Nothing is playing")
    
    @commands.command(name="resume")
    async def resume(self, context: Context):
        ''' Resume the audio '''
        if context.voice_client is None:
            await context.send("I am not in a voice channel")
            return
        if context.voice_client.is_paused():
            context.voice_client.resume()
            await context.send("Resumed")
        else:
            await context.send("Nothing is paused")
    
    @commands.command(name="stop")
    async def stop(self, context: Context):
        ''' Stop the audio '''
        if context.voice_client is None:
            await context.send("I am not in a voice channel")
            return
        if context.voice_client.is_playing():
            context.voice_client.stop()
            await context.send("Stopped")
        else:
            await context.send("Nothing is playing")


async def setup(bot):
    await bot.add_cog(Voice(bot))


