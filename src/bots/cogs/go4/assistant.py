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

        google_api_key = os.environ['GOOGLE_API_KEY']
        # llm with gemini model
        self.llm = Gemini(
            model="models/gemini-2.0-flash",
            api_key=google_api_key
        )
        self.open_conversations = dict()
        self.tools_available = dict()
        self.load_tools_available()
    
    def get_llm_response(self, query, chat_history=None, guild_id=None):
        ''' Get response from LLM with optional chat history '''
        role_prompt = (
            "You are an assistant agent in a Discord bot, working alongside other bots. "
            "When a user asks for something, respond concisely and helpfully. "
            "You can use tools (other bots) by sending their commands with the correct prefix."
        )
        tool_prompt = ""
        if guild_id and str(guild_id) in self.tools_available:
            header_lines = [
               "Tool Usage Rules:",
                "- Use tool commands only when necessary.",
                "- DO NOT wrap commands in backticks, quotes, or any formatting.",
                "- Send them exactly as: <prefix><command> [arguments if needed]",
                "- Example: If the prefix is &&, just send: &&command_name",
            ]
            for bot_name, meta in self.tools_available[str(guild_id)].items():
                prefix = meta.get("prefix", "")
                commands = meta.get("commands", {})
                for category, cmds in commands.items():
                    header_lines.append(f"\n**{bot_name} - {category}**")
                    for cmd, info in cmds.items():
                        description = info.get("description", "No description available")
                        header_lines.append(f"{prefix}{cmd} - {description}")
            tool_prompt = "\n".join(header_lines) + "\n\n"

        full_prompt = "role:" + role_prompt + "\n\n" + tool_prompt   
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
                    response = self.get_llm_response(message.content, chat_history, message.guild.id)
                except ValueError as e:
                    embed = discord.Embed(
                        title="I'm Sorry! :confused:",
                        description='The query is getting too long. Please end the chat session and start a new one. If not, try to clear up the tools list using the command `clear_tools`.',
                        color=self.bot.default_color,
                    )
                    await message.reply(embed=embed)
                    return
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
    async def read_help(self, context: Context, prefix: str, category: str = None):
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
        bot_name, help_embed = await self.wait_for_response(context)
        if not help_embed:
            embed = discord.Embed(
                title='Timeout :stopwatch:',
                description='No help embed received within the timeout period. Please try again.',
                color=self.bot.default_color,
            )
            await context.reply(embed=embed)
            return
        commands = self.parse_help_embed(help_embed, category)
        guild_id = context.guild.id
        if len(commands) == 0:
            embed = discord.Embed(
                title='No Commands Found :mag:',
                color=self.bot.default_color,
            )
            if category:
                embed.description = f"No commands found in category '{category}' from {bot_name} with prefix `{prefix}`."
            else:
                embed.description=f'No commands found in the help embed from {bot_name}. Please check the prefix and try again.',
            await context.reply(embed=embed)
            return
        if str(guild_id) not in self.tools_available:
            self.tools_available[str(guild_id)] = {}
        if bot_name not in self.tools_available[str(guild_id)]:
            self.tools_available[str(guild_id)][bot_name] = dict()
        self.tools_available[str(guild_id)][bot_name]["prefix"] = prefix
        if "commands" not in self.tools_available[str(guild_id)][bot_name]:
            self.tools_available[str(guild_id)][bot_name]["commands"] = commands
        if category is not None:
            self.tools_available[str(guild_id)][bot_name]["commands"].update(commands)
        self.save_tools_available()

        embed = discord.Embed(
            title=f'Help from {bot_name} :books:',
            color=self.bot.default_color,
        )
        if category:
            embed.description = f"Category: {category} has been read from {bot_name} with prefix `{prefix}` and all its tools have been saved."
        else:
            embed.description = f"{bot_name} has been read with prefix `{prefix}` and all its tools have been saved. {len(commands)} categories found."
        await context.reply(embed=embed)
    
    @commands.command(name='clear_tools', description='clear tools available list for the agent')
    async def clear_tools(self, context: Context):
        self.delete_tools_available_data(context.guild.id)
        embed = discord.Embed(
            title='Tools Cleared :wastebasket:',
            description='All tools have been cleared for this server.',
            color=self.bot.default_color,
        )
        await context.reply(embed=embed)

    async def wait_for_response(self, context, bot=False, timeout=15) -> discord.Embed:
        '''Wait for the next embed message from another bot.'''
        def check(m: discord.Message):
            return (
                m.channel == context.channel and
                m.author != context.me and
                m.author.bot if bot else True and
                len(m.embeds) > 0
            )
        try:
            msg = await self.bot.wait_for("message", check=check, timeout=timeout)
            author_name = msg.author.name if msg.author else "Unknown"
            return (author_name, msg.embeds[0])
        except asyncio.TimeoutError:
            return None
    
    def parse_help_embed(self, embed: discord.Embed, category: str = None):
        '''Extract command info from a help embed.'''
        
        commands = dict()
        # General help parsing (lists all commands)
        for field in embed.fields:
            if category and field.name.lower() != category.lower():
                continue
            commands[field.name] = dict()
            for line in field.value.split('\n'):
                # Extract command name and description from lines like:
                # ***`watchlist`*** - Shows your movie watchlist
                # or with aliases: ***`command`*** **(`a1`)** **(`a2`)** - Description
                if '***`' in line:
                    # Extract command name (first backtick block)
                    command_name = line.split('***`')[1].split('`***')[0].strip()
                    # Extract description (everything after the last hyphen)
                    description = line.split('-')[-1].strip() if '-' in line else "No description"
                    commands[field.name][command_name] = {
                        "description": description
                    }
        return commands

    def save_tools_available(self):
        if os.path.exists(self.bot.data_dir):
            for guild_id, bot_names in self.tools_available.items():
                guild_path = os.path.join(self.bot.data_dir, str(guild_id), 'tools_available')
                os.makedirs(guild_path, exist_ok=True)
                for bot_name , meta in bot_names.items():
                    file_path = os.path.join(guild_path, f"{bot_name}.yml")
                    with open(file_path, 'w') as file:
                        yaml.dump(meta, file, default_flow_style=False)
                self.bot.log.info(f'Saved tools available for guild {guild_id}', guild=self.bot.get_guild(guild_id))
    
    def delete_tools_available_data(self, guild_id):
        ''' Delete tools available for a guild '''
        if str(guild_id) in self.tools_available:
            del self.tools_available[str(guild_id)]
            guild_path = os.path.join(self.bot.data_dir, str(guild_id), 'tools_available')
            if os.path.exists(guild_path):
                for file in os.listdir(guild_path):
                    os.remove(os.path.join(guild_path, file))
                os.rmdir(guild_path)
            self.bot.log.info(f'Deleted tools available for guild {guild_id}', guild=self.bot.get_guild(guild_id))
               
    def load_tools_available(self):
        if os.path.exists(self.bot.data_dir):
            guilds = [d for d in os.listdir(self.bot.data_dir) if os.path.isdir(os.path.join(self.bot.data_dir, d))]
            for guild_id in guilds:
                tools_path = os.path.join(self.bot.data_dir, guild_id, 'tools_available')
                if os.path.exists(tools_path):
                    for file in os.listdir(tools_path):
                        if file.endswith('.yml'):
                            bot_name = file.split('.')[0]
                            file_path = os.path.join(tools_path, file)
                            with open(file_path, 'r') as f:
                                meta = yaml.safe_load(f)
                                if guild_id not in self.tools_available:
                                    self.tools_available[str(guild_id)] = dict()
                                self.tools_available[str(guild_id)][bot_name] = meta
                                self.bot.log.info(f'Loaded tools available for guild {guild_id} - {bot_name}')
                            
async def setup(bot):
    await bot.add_cog(Assistant(bot))