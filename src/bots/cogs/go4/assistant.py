#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Command related to llm assistant '''

#-------------------------------------------------------------------------------

import os
import yaml
import discord
import textwrap
import asyncio
import aiohttp
from discord.ext import commands
from discord.ext.commands import Context
from llama_index.llms.gemini import Gemini

class Assistant(commands.Cog, name="Chatting Features"):
    def __init__(self, bot):
        self.bot = bot
        self.conversation_limit = 8  # Limit for conversation history
        google_api_key = os.environ['GOOGLE_API_KEY']
        # llm with gemini model
        self.llm = Gemini(
            model="models/gemini-2.0-flash",
            api_key=google_api_key
        )
        self.open_conversations = dict()
    
    def get_llm_response(self, query, chat_history=None, author_name=None):
        ''' Get response from LLM with optional chat history '''
        role_prompt = (
            f"Your name is {self.bot.name} ",
            "You are a helpful assistant inside a Discord bot. "
        )
        full_prompt = "role: " + "\n-".join(role_prompt) + "\n"
        if author_name:
            full_prompt += f"The user's name is {author_name}. "
        if chat_history:
            formatted_history = "\n".join(f"User: {msg[0]}\nAssistant: {msg[1]}" for msg in chat_history)
            query = f"{full_prompt}Chat History:\n{formatted_history}\n\nNew User Message: {query}"
        else:
            query = f"{full_prompt}\n\nNew User Message: {query}"
        # save the query for debugging
        # with open(os.path.join(self.bot.data_dir, 'query.txt'), 'a') as f:
        #     f.write(f"Query: {query}\n")
        if len(query) > 4000: # check if the query is too long
            raise ValueError("Query is getting too long ...")
        response = self.llm.complete(query)
        return str(response)

    @commands.command(name='chat', description='Open a conversation with bot', aliases=['c'])
    async def chat(self, context: Context):
        ''' Chat with the bot '''
        channel = context.channel
        author = context.author
        # Initialize chat history for this user in this channel
        if channel not in self.open_conversations:
            self.open_conversations[channel] = {}
        
        if author in self.open_conversations[channel]:
            embed = discord.Embed(
                title='Already Chatting! :speech_balloon:',
                description="You already have an active chat session in this channel.",
                color=self.bot.default_color,
            )
            await context.reply(embed=embed)
            return
        # Initialize empty chat history
        self.open_conversations[channel][author] = []
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
        
        if channel in self.open_conversations and author in self.open_conversations[channel]:
            del self.open_conversations[channel][author]
            if not self.open_conversations[channel]:  # If no more users in this channel
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
    
    @commands.command(name='end_all_chat', description='End all active chat sessions')
    @commands.is_owner()
    async def endall(self, context: Context):
        ''' End all active chat sessions '''
        count = sum(len(users) for users in self.open_conversations.values())
        self.open_conversations.clear()
        
        embed = discord.Embed(
            title='All Chats Ended :wave:',
            description=f'Successfully closed {count} active chat sessions.',
            color=self.bot.default_color,
        )
        await context.reply(embed=embed)
        self.bot.log.info(f'Ended all {count} active chat sessions', guild=context.guild)

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
        channel = message.channel
        author = message.author
        if channel in self.open_conversations and author in self.open_conversations[channel]:
            if message.content.lower() == 'end':
                del self.open_conversations[channel][author]
                if not self.open_conversations[channel]:  # If no more users in this channel
                    del self.open_conversations[channel]
                embed = discord.Embed(
                    title='Closing Chat :wave:',
                    description='The chat session has been ended.',
                    color=self.bot.default_color,
                )
                await message.reply(embed=embed)
                self.bot.log.info(f'Ended chat session with {author.name} in {channel.name}', guild=message.guild)
            else:
                # Get chat history for this user
                chat_history = self.open_conversations[channel][author] 
                try:
                    # Get response from LLM with chat history
                    response = self.get_llm_response(message.content, chat_history, author_name=author.display_name)
                except ValueError as e:
                    chat_history.pop()  # Remove oldest message already in history
                    embed = discord.Embed(
                        title="I'm Sorry! :confused:",
                        description='The query is getting too long. Please end the chat session and start a new one.',
                        color=self.bot.default_color,
                    )
                    await message.reply(embed=embed)
                    return
                # Add this exchange to chat history (keeping last N messages if you want to limit)
                chat_history.append((message.content, response))
                # Limit chat history length to prevent memory issues
                if len(chat_history) > self.conversation_limit: 
                    chat_history.pop(0)
                # Send response
                parts = self.split_message(response)
                for part in parts:
                    await message.reply(part)
                self.bot.log.info(f'Responded to {author.name} in {channel.name}', guild=message.guild)
                            
async def setup(bot):
    await bot.add_cog(Assistant(bot))
