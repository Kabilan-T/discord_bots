#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Command related to llm assistant '''

#-------------------------------------------------------------------------------

import os
import discord
import textwrap
from discord.ext import commands
from discord.ext.commands import Context
from llama_index.llms.gemini import Gemini

class Assistant(commands.Cog, name="Chatting Features"):
    def __init__(self, bot):
        self.bot = bot

        google_api_key = os.environ['GOOGLE_API_KEY']
        # llm with gemini model
        self.llm = Gemini(
            model="models/gemini-2.0-flash",
            api_key=google_api_key
        )
        self.open_conversations = dict()
    
    def get_llm_response(self, query):
        ''' Get response from LLM '''
        response = self.llm.complete(query)
        return str(response)

    @commands.command(name='chat', description='Open a conversation with bot', aliases=['c'])
    async def chat(self, context: Context):
        ''' Chat with the bot '''
        channel = context.channel
        author = context.author
        if channel in self.open_conversations.keys():
            self.open_conversations[channel].append(author)
        else:
            self.open_conversations[channel] = [author]
        embed = discord.Embed(
            title='Let\'s Chat! :speech_balloon:',
            description="Hello! I have opened a chat session with you in this channel",
            color=self.bot.default_color,
        )
        embed.set_footer(text=f"Type 'end' or use the command `{self.bot.prefix[context.guild.id]}end` to end the chat session.")
        await context.reply(embed=embed)
        self.bot.log.info(f'Started chat session with {author.name} in {channel.name}', guild=context.guild)
    
    @commands.command(name='end', description='End the chat session', aliases=['e'])
    async def end(self, context: Context):
        ''' End the chat session '''
        channel = context.channel
        author = context.author
        if channel in self.open_conversations.keys():
            if author in self.open_conversations[channel]:
                self.open_conversations[channel].remove(author)
                if len(self.open_conversations[channel]) == 0:
                    del self.open_conversations[channel]
                embed = discord.Embed(
                    title='Closing Chat :wave:',
                    description='The chat session has been ended.',
                    color=self.bot.default_color,
                )
                await context.reply(embed=embed)
                self.bot.log.info(f'Ended chat session with {author.name} in {channel.name}', guild=context.guild)
            else:
                embed = discord.Embed(
                    title='Sorry! :confused:',
                    description='You do not have an active chat session in this channel.',
                    color=self.bot.default_color,
                )
                await context.reply(embed=embed)
                self.bot.log.warning(f'{author.name} tried to end a chat session without an active session in {channel.name}', guild=context.guild)
                return
        else:
            embed = discord.Embed(
                title='Sorry! :confused:',
                description='There is no active chat session in this channel.',
                color=self.bot.default_color,
            )
            await context.reply(embed=embed)
            self.bot.log.warning(f'{author.name} tried to end a chat session without an active session in {channel.name}', guild=context.guild)
            return
    def split_message(self, text, limit=2000):
        '''Split text by newlines and words, respecting the character limit.'''
        parts = list()
        current = str()
        for line in text.split('\n'):
            if len(current) + len(line) + 1 > limit:
                if current:
                    parts.append(current)
                    current = str()
                if len(line) > limit:
                    wrapped_lines = textwrap.wrap(line, width=limit, break_long_words=False, break_on_hyphens=False)
                    parts.extend(wrapped_lines)
                else:
                    current = line
            else:
                current = current + '\n' + line if current else line
        if current:
            parts.append(current)
        return parts
    
    @commands.Cog.listener()
    async def on_message(self, message):
        ''' Listen for messages '''
        if message.author == self.bot.user:
            return
        if message.content.startswith(self.bot.prefix[message.guild.id]):
            return
        if message.channel in self.open_conversations.keys():
            if message.author in self.open_conversations[message.channel]:
                if message.content.lower() == 'end':
                    self.open_conversations[message.channel].remove(message.author)
                    if len(self.open_conversations[message.channel]) == 0:
                        del self.open_conversations[message.channel]
                    embed = discord.Embed(
                        title='Closing Chat :wave:',
                        description='The chat session has been ended.',
                        color=self.bot.default_color,
                    )
                    await message.reply(embed=embed)
                    self.bot.log.info(f'Ended chat session with {message.author.name} in {message.channel.name}', guild=message.guild)
                else:
                    response = self.get_llm_response(message.content)
                    parts = self.split_message(response)
                    for part in parts:
                        await message.reply(part)

                    self.bot.log.info(f'Responded to {message.author.name} in {message.channel.name}', guild=message.guild)

async def setup(bot):
    await bot.add_cog(Assistant(bot))