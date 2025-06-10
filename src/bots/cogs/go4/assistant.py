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
import asyncio
import aiohttp
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
        self.open_conversations = dict()  # {channel: {user: [messages]}}
        self.tools_available = dict()
    
    def get_llm_response(self, query, chat_history=None, guild_id=None):
        ''' Get response from LLM with optional chat history '''
        tool_prompt = ""
        if guild_id and guild_id in self.tools_available:
            header_lines = [
                "You can use the following available tools by invoking their commands.",
                "If a tool has arguments, use the appropriate syntax as shown.",
                "Remove any ` ` block or ``` ``` block in the output if using a tool"
            ]
            for prefix, cmds in self.tools_available[guild_id].items():
                for cmd, meta in cmds.items():
                    desc = meta.get("description", "No description")
                    usage = meta.get("usage", f"{prefix}{cmd}")
                    header_lines.append(f"- {cmd}: {desc}\n  Usage: {usage}")
            tool_prompt = "\n".join(header_lines) + "\n\n"
        if chat_history:
            formatted_history = "\n".join(f"User: {msg[0]}\nAssistant: {msg[1]}" for msg in chat_history)
            query = f"{tool_prompt}Chat History:\n{formatted_history}\n\nNew User Message: {query}"
        else:
            query = f"{tool_prompt}{query}"
        
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
                
                # Get response from LLM with chat history
                response = self.get_llm_response(message.content, 
                                                 chat_history,
                                                 message.guild.id)
                
                # Add this exchange to chat history (keeping last N messages if you want to limit)
                chat_history.append((message.content, response))
                # Limit chat history length to prevent memory issues
                if len(chat_history) > 10:  # Keep last n exchanges
                    chat_history.pop(0)
                
                # Send response
                parts = self.split_message(response)
                for part in parts:
                    await message.reply(part)

                self.bot.log.info(f'Responded to {author.name} in {channel.name}', guild=message.guild)

    
    @commands.command(name='read', description='Scrape another bot\'s help command')
    async def read_help(self, context: Context, prefix: str):
        ''' Scrape another bot's help command '''
        if not prefix:
            embed = discord.Embed(
                title='Error :x:',
                description='Please provide a prefix to scrape help from another bot.',
                color=self.bot.default_color,
            )
            await context.reply(embed=embed)
            return
        await context.reply(f"{prefix}help")

        help_embed = await self._wait_for_help_embed(context)
        if not help_embed:
            embed = discord.Embed(
                title='Timeout :stopwatch:',
                description='No help embed received within the timeout period. Please try again.',
                color=self.bot.default_color,
            )
            await context.reply(embed=embed)
            return

        bot_name, commands = self._parse_help_embed(help_embed)
        embed = discord.Embed(
            title=f'Help from {bot_name} :books:',
            description=f'I have read {len(commands)} commands',
            color=self.bot.default_color,
        )
        guild_id = context.guild.id
        if guild_id not in self.tools_available:
            self.tools_available[guild_id] = {}
        self.tools_available[guild_id][prefix] = commands
        await context.reply(embed=embed)
    
    @commands.command(name='clear_tools', description='clear tools available list for the agent')
    async def clear_tools(self, context: Context):
        self.tools_available.pop(context.guild.id, None)
        embed = discord.Embed(
            title='Tools Cleared :wastebasket:',
            description='All tools have been cleared for this server.',
            color=self.bot.default_color,
        )
        await context.reply(embed=embed)

    async def _wait_for_help_embed(self, context, timeout=15) -> discord.Embed:
        '''Wait for the next embed message from another bot.'''
        def check(m: discord.Message):
            return (
                m.channel == context.channel and
                m.author != context.me and
                m.author.bot and
                len(m.embeds) > 0
            )
        try:
            msg = await self.bot.wait_for("message", check=check, timeout=timeout)
            return msg.embeds[0]
        except asyncio.TimeoutError:
            return None
    
    def _parse_help_embed(self, embed: discord.Embed) -> tuple[str, dict]:
        '''Extract command info from a help embed.'''
        bot_name = embed.author.name if embed.author else "Unknown Bot"
        commands = {}

        # Case 1: Specific command help (has 'Usage' field)
        if any(field.name == "Usage" for field in embed.fields):
            command_name = embed.title.replace("Help: ", "").strip()
            commands[command_name] = {
                "description": embed.description,
                "usage": embed.fields[0].value  # First field is 'Usage'
            }
            return (bot_name, commands)

        # Case 2: General help (lists all commands)
        for field in embed.fields:
            # Each field is a cog with command listings
            for line in field.value.split('\n'):
                # Extract command name and description from lines like:
                # ***`watchlist`*** - Shows your movie watchlist
                # or with aliases: ***`command`*** **(`a1`)** **(`a2`)** - Description
                if '***`' in line:
                    # Extract command name (first backtick block)
                    command_name = line.split('***`')[1].split('`***')[0].strip()
                    # Extract description (everything after the last hyphen)
                    description = line.split('-')[-1].strip() if '-' in line else "No description"
                    # Extract aliases if present
                    aliases = []
                    if '**(`' in line:
                        alias_part = line.split('`***')[-1].split('-')[0]
                        aliases = [a.split('`')[1] for a in alias_part.split('**(`')[1:]]
                    commands[command_name] = {
                        "description": description,
                        "aliases": aliases,
                        "category": field.name
                    }
        return (bot_name, commands)

async def setup(bot):
    await bot.add_cog(Assistant(bot))