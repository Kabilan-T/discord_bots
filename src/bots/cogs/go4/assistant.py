#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Command related to llm assistant '''

#-------------------------------------------------------------------------------

import asyncio
import functools
import discord
import textwrap
from datetime import datetime
from collections import OrderedDict
from discord.ext import commands
from discord.ext.commands import Context
from .utils.llm_workflow_graph import get_agent_response


class Assistant(commands.Cog, name="Chatting Features"):
    def __init__(self, bot):
        self.bot = bot
        # {conv_id: {user, guild_id, channel_id, history, created_at}}
        self.conversations = OrderedDict()
        # {bot_message_id: conv_id} — tracks which bot messages belong to which conversation
        self.message_to_conv = {}

    def _make_conv_id(self, username: str) -> str:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S-%f")  # microseconds avoids same-second collisions
        return f"{ts}-{username}"

    async def _call_llm(self, question: str, display_name: str, history: list):
        '''Run the blocking LLM call in a thread pool.'''
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            functools.partial(get_agent_response, question, display_name, history)
        )

    async def _send_response(self, response: str, reply_target) -> list:
        '''Split and send a response, returning all sent message objects.'''
        parts = self.split_message(response)
        sent = []
        for i, part in enumerate(parts):
            if i == 0:
                msg = await reply_target.reply(part)
            else:
                msg = await reply_target.channel.send(part)
            sent.append(msg)
        return sent

    @commands.command(name='ask', description='Ask the bot a question', aliases=['a'])
    async def ask(self, context: Context, *, question: str):
        ''' Ask the LLM a question. Reply to its response to continue the conversation. '''
        conv_id = self._make_conv_id(context.author.display_name)

        async with context.channel.typing():
            try:
                response, history = await self._call_llm(question, context.author.display_name, [])
            except Exception as e:
                embed = discord.Embed(
                    title="I'm Sorry! :confused:",
                    description='Something went wrong while generating a response. Please try again.',
                    color=self.bot.default_color,
                )
                await context.reply(embed=embed)
                self.bot.log.warning(f'LLM error for {context.author.name}: {e}', guild=context.guild)
                return

        self.conversations[conv_id] = {
            'user': context.author.display_name,
            'guild_id': context.guild.id,
            'channel_id': context.channel.id,
            'history': history,
            'created_at': datetime.now(),
        }

        sent_messages = await self._send_response(response, context)
        for msg in sent_messages:
            self.message_to_conv[msg.id] = conv_id

        self.bot.log.info(f'New conversation {conv_id} started by {context.author.name}', guild=context.guild)

    @ask.error
    async def ask_error(self, context: Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title='Missing Question',
                description=f'Usage: `{self.bot.prefix[context.guild.id]}ask <your question>`',
                color=self.bot.default_color,
            )
            await context.reply(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        ''' Continue a conversation when someone replies to a bot response. '''
        if message.author == self.bot.user:
            return
        if message.guild is None:
            return
        if message.content.startswith(self.bot.prefix[message.guild.id]):
            return
        if not message.reference:
            return
        if not message.content.strip():
            return  # attachment/sticker-only reply, nothing to send to LLM

        conv_id = self.message_to_conv.get(message.reference.message_id)
        if not conv_id or conv_id not in self.conversations:
            return

        conv = self.conversations[conv_id]

        async with message.channel.typing():
            try:
                response, updated_history = await self._call_llm(
                    message.content, message.author.display_name, conv['history']
                )
            except Exception as e:
                embed = discord.Embed(
                    title="I'm Sorry! :confused:",
                    description='Something went wrong while generating a response. Please try again.',
                    color=self.bot.default_color,
                )
                await message.reply(embed=embed)
                self.bot.log.warning(f'LLM error in conversation {conv_id}: {e}', guild=message.guild)
                return

        conv['history'] = updated_history

        sent_messages = await self._send_response(response, message)
        for msg in sent_messages:
            self.message_to_conv[msg.id] = conv_id

        self.bot.log.info(f'Continued conversation {conv_id} by {message.author.name}', guild=message.guild)

    @commands.command(name='chats', description='List all tracked conversations')
    async def list_chats(self, context: Context):
        ''' List all active LLM conversations in this server '''
        guild_convs = [(cid, conv) for cid, conv in self.conversations.items()
                       if conv['guild_id'] == context.guild.id]

        if not guild_convs:
            embed = discord.Embed(
                title='No Conversations',
                description='There are no tracked conversations in this server.',
                color=self.bot.default_color,
            )
            await context.reply(embed=embed)
            return

        lines = []
        for i, (conv_id, conv) in enumerate(guild_convs, 1):
            ts = conv['created_at'].strftime("%Y-%m-%d %H:%M:%S")
            msg_count = len(conv['history'])
            lines.append(f"`{i}.` **{conv['user']}** — {ts} ({msg_count} messages) `{conv_id}`")

        embed = discord.Embed(
            title=f'Conversations ({len(guild_convs)})',
            description='\n'.join(lines),
            color=self.bot.default_color,
        )
        await context.reply(embed=embed)

    @commands.command(name='clear_chat', description='Clear a conversation by its list number')
    async def clear_chat(self, context: Context, sl_no: int):
        ''' Clear a specific conversation (use the number from the chats list) '''
        conv_list = [cid for cid, conv in self.conversations.items()
                     if conv['guild_id'] == context.guild.id]
        if not conv_list:
            embed = discord.Embed(
                title='No Conversations',
                description='There are no tracked conversations to clear.',
                color=self.bot.default_color,
            )
            await context.reply(embed=embed)
            return
        if sl_no < 1 or sl_no > len(conv_list):
            embed = discord.Embed(
                title='Invalid Number',
                description=f'Please provide a number between 1 and {len(conv_list)}.',
                color=self.bot.default_color,
            )
            await context.reply(embed=embed)
            return

        conv_id = conv_list[sl_no - 1]
        to_remove = [mid for mid, cid in self.message_to_conv.items() if cid == conv_id]
        for mid in to_remove:
            del self.message_to_conv[mid]
        del self.conversations[conv_id]

        embed = discord.Embed(
            title='Conversation Cleared :wastebasket:',
            description=f'Removed conversation `{conv_id}`.',
            color=self.bot.default_color,
        )
        await context.reply(embed=embed)
        self.bot.log.info(f'Cleared conversation {conv_id}', guild=context.guild)

    @commands.command(name='clear_all_chats', description='Clear all tracked conversations')
    @commands.is_owner()
    async def clear_all_chats(self, context: Context):
        ''' Clear all tracked conversations (owner only) '''
        count = len(self.conversations)
        self.conversations.clear()
        self.message_to_conv.clear()

        embed = discord.Embed(
            title='All Conversations Cleared :wastebasket:',
            description=f'Removed {count} conversation(s).',
            color=self.bot.default_color,
        )
        await context.reply(embed=embed)
        self.bot.log.info(f'Cleared all {count} conversations', guild=context.guild)

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


async def setup(bot):
    await bot.add_cog(Assistant(bot))
