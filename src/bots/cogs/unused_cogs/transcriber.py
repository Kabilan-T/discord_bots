#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' This cogs contains commands related to the transcriber bot '''

#-------------------------------------------------------------------------------

import os
import wave
import datetime
import asyncio
import speech_recognition as sr
import discord
from discord.ext import commands
from discord.ext.commands import Context
import discord.ext.voice_recv as voice_recv
from discord.ext.voice_recv.extras.speechrecognition import SpeechRecognitionSink

discord.opus._load_default()


class Transcriber(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(name="test_transcribe", aliases=["tt"])
    async def test(self, context, duration: int):
        
        received_text = []

        def got_text(user: discord.User, text: str):
            if text:
                print(f"Text from {user.name}: {text}")
                received_text.append((user.name, text))
                # Schedule the coroutine safely on the main loop
                # future = asyncio.run_coroutine_threadsafe(
                #     context.send(f"{user.display_name} said: {text}"),
                #     self.bot.loop
                # )
                
        voice_client = await context.author.voice.channel.connect(cls=voice_recv.VoiceRecvClient)

        # voice_client.listen(voice_recv.BasicSink(callback))
        voice_client.listen(SpeechRecognitionSink( default_recognizer="google", 
                                                   text_cb= got_text))
                                
                            
        # Wait for the specified duration
        await asyncio.sleep(duration)

        # Stop listening and disconnect
        voice_client.stop_listening()

        for user, text in received_text:
            await context.send(f"{user} said: {text}")

        await voice_client.disconnect()
        await context.send("Transcription completed and bot disconnected.")



    @commands.command(name="stop2")
    async def stop(self, context):
        await context.voice_client.disconnect()


async def setup(bot):
    await bot.add_cog(Transcriber(bot))
