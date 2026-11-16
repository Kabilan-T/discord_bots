#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# Github: Kabilan-T

''' GO-4 assistant: AI chat channel, ask/reply conversations, tools and other-bot coordination '''

#-------------------------------------------------------------------------------

import os
import time
import asyncio
import textwrap
import aiohttp
import discord
import anthropic
from datetime import datetime
from collections import OrderedDict
from zoneinfo import ZoneInfo
from discord.ext import commands
from discord.ext.commands import Context
from bots.cogs.bridge import load_full_config, load_bridge_registry, get_bridge_secret, get_guild_prefix
from .utils.llm_agent import Agent, Conversation
from .utils.tools import ToolContext, ToolError

DEFAULTS = {'model': 'claude-haiku-5-5', 'effort': 'low'}  # overridable in config.yml go4.assistant
TIMEZONE = 'UTC'            # clock times without a zone are UTC; replies add Discord timestamp tags for local time
MAX_TOKENS = 1024           # output cap per model call (replies are short)
REQUEST_TIMEOUT = 60        # seconds
MAX_TOOL_STEPS = 4          # tool rounds per message
MAX_HISTORY_TURNS = 20      # remembered exchanges per conversation (in memory only)
MAX_HISTORY_TOKENS = 6000   # approx cap on remembered history (oldest exchanges dropped first)
MAX_INPUT_CHARS = 1500      # longer user messages are cut before being sent to the model
MAX_CONVERSATIONS = 200
RESET_WORDS = {'reset', 'new chat', 'clear chat'}
SETTINGS_FILE = 'assistant.yml'
USAGE_FILE = 'ai_usage.yml'


class Assistant(commands.Cog, name="Chatting Features"):
    def __init__(self, bot):
        self.bot = bot
        full_config = load_full_config()
        conf = {**DEFAULTS, **((full_config.get(bot.bot_name, {}) or {}).get('assistant') or {})}
        self.tz = ZoneInfo(TIMEZONE)
        api_key = os.environ.get('ANTHROPIC_API_KEY', '')
        self.client = None
        if api_key.startswith('sk-ant-'):
            self.client = anthropic.AsyncAnthropic(api_key=api_key, timeout=REQUEST_TIMEOUT, max_retries=2)
        else:
            bot.log.error('GO-4: ANTHROPIC_API_KEY is not set in tokens.sh; the assistant is disabled')
        self.agent = Agent(self.client, conf['model'], self.tz, effort=conf['effort'], max_tokens=MAX_TOKENS,
                           max_steps=MAX_TOOL_STEPS, max_turns=MAX_HISTORY_TURNS,
                           max_history_tokens=MAX_HISTORY_TOKENS, log=bot.log)
        self.bridge_bots = {key: info for key, info in load_bridge_registry().items() if key != bot.bot_name}
        self.all_prefixes = {c['default_prefix'] for c in full_config.values()
                             if isinstance(c, dict) and c.get('default_prefix')}
        self.conversations = OrderedDict()   # {conv_id: Conversation}
        self.message_to_conv = dict()        # {GO-4 message id: conv_id}
        self.reminders = dict()              # {id: {...}} used by tools
        self.ai_channels = dict()            # {guild_id: channel_id}
        self.prefix_cache = dict()           # {guild_id: (timestamp, {bot_key: prefix})}
        self.commands_cache = dict()         # {guild_id: (timestamp, text)}
        self.http = None
        self.bridge_secret = None

    async def cog_load(self):
        self.http = aiohttp.ClientSession()
        try:
            self.bridge_secret = get_bridge_secret()
        except Exception as e:
            self.bot.log.error(f'GO-4 could not read the bridge secret: {e}')
        for guild_id in self.bot.list_guild_ids():
            channel_id = self.bot.load_guild_yaml(guild_id, SETTINGS_FILE).get('ai_channel')
            if channel_id:
                self.ai_channels[guild_id] = int(channel_id)

    async def cog_unload(self):
        for reminder in self.reminders.values():
            reminder['task'].cancel()
        if self.http is not None:
            await self.http.close()
        if self.client is not None:
            await self.client.close()

    # ---- usage tracking ---------------------------------------------------------

    def record_usage(self, result):
        '''Add a reply's tokens to this month's totals (src/data/GO-4/bot/ai_usage.yml)'''
        month = datetime.now(self.tz).strftime('%Y-%m')
        usage = self.bot.load_bot_yaml(USAGE_FILE)
        row = usage.setdefault(month, {'replies': 0, 'calls': 0, 'input_tokens': 0, 'output_tokens': 0,
                                       'cache_write_tokens': 0, 'cache_read_tokens': 0})
        row['replies'] += 1
        row['calls'] += result.calls
        row['input_tokens'] += result.input_tokens
        row['output_tokens'] += result.output_tokens
        row['cache_write_tokens'] += result.cache_write_tokens
        row['cache_read_tokens'] += result.cache_read_tokens
        self.bot.save_bot_yaml(USAGE_FILE, usage)

    # ---- bridge client --------------------------------------------------------

    async def bridge_call(self, info: dict, method: str, path: str, params=None, json=None):
        if not self.bridge_secret:
            raise ToolError('the bot bridge is not configured')
        url = f"http://127.0.0.1:{info['port']}{path}"
        try:
            async with self.http.request(method, url, params=params, json=json,
                                         headers={'X-Bridge-Secret': self.bridge_secret},
                                         timeout=aiohttp.ClientTimeout(total=90)) as response:
                if response.status == 401:
                    raise ToolError('bridge authentication failed')
                return await response.json(content_type=None)
        except aiohttp.ClientConnectionError:
            raise ToolError(f"{info['name']} is offline (could not reach it)")
        except asyncio.TimeoutError:
            raise ToolError(f"{info['name']} did not answer in time")

    async def _bot_commands_text(self, guild_id: int) -> str:
        '''Compact command list of every bridged bot (cached 5 minutes)'''
        cached = self.commands_cache.get(guild_id)
        if cached and time.time() - cached[0] < 300:
            return cached[1]

        async def fetch(info):
            try:
                data = await asyncio.wait_for(
                    self.bridge_call(info, 'GET', '/commands', params={'guild_id': str(guild_id)}), timeout=5)
                lines = [f"  {c['usage']} — {c['description']}" for c in data.get('commands', [])]
                return f"{info['name']} ({info['about']}):\n" + '\n'.join(lines)
            except Exception as e:
                return f"{info['name']}: currently unreachable ({e})"

        blocks = await asyncio.gather(*(fetch(info) for info in self.bridge_bots.values()))
        text = '\n'.join(blocks)
        if 'unreachable' not in text:  # don't cache a partial list
            self.commands_cache[guild_id] = (time.time(), text)
        return text

    async def live_context(self, guild: discord.Guild, requester: discord.Member) -> str:
        '''Facts GO-4 would otherwise spend tool calls on: bot commands and voice state'''
        voice = f"{requester.display_name} is in voice channel '{requester.voice.channel.name}'" \
            if requester.voice and requester.voice.channel else f'{requester.display_name} is NOT in a voice channel'
        bot_voice = list()
        for info in self.bridge_bots.values():
            member = guild.get_member(int(info['client_id'])) if info.get('client_id') else None
            if member is None:
                bot_voice.append(f"{info['name']}: not in this server")
            elif member.voice and member.voice.channel:
                bot_voice.append(f"{info['name']}: in '{member.voice.channel.name}'")
            else:
                bot_voice.append(f"{info['name']}: not in voice")
        commands_text = await self._bot_commands_text(guild.id)
        return (f'Voice right now: {voice}. Bots: ' + '; '.join(bot_voice) + '.\n\n'
                f'Commands of the other bots (use with run_bot_command, without the prefix):\n{commands_text}')

    # ---- conversations --------------------------------------------------------

    def _remember(self, conv_id: str, conv: Conversation):
        self.conversations[conv_id] = conv
        self.conversations.move_to_end(conv_id)
        while len(self.conversations) > MAX_CONVERSATIONS:
            old_id, _ = self.conversations.popitem(last=False)
            self._forget_messages(old_id)

    def _forget_messages(self, conv_id: str):
        for message_id in [mid for mid, cid in self.message_to_conv.items() if cid == conv_id]:
            del self.message_to_conv[message_id]

    def _channel_conv(self, message: discord.Message):
        conv_id = f'channel-{message.channel.id}'
        conv = self.conversations.get(conv_id)
        if conv is None:
            conv = Conversation(message.channel.name, message.guild.id, message.channel.id, 'channel')
            self._remember(conv_id, conv)
        return conv_id, conv

    def bot_prefixes(self, guild_id: int) -> dict:
        '''{bot_key: prefix} of the other bots in this guild (cached for a minute)'''
        cached = self.prefix_cache.get(guild_id)
        if cached and time.time() - cached[0] < 60:
            return cached[1]
        prefixes = {key: get_guild_prefix(key, guild_id) for key in self.bridge_bots}
        self.prefix_cache[guild_id] = (time.time(), prefixes)
        return prefixes

    def _is_command(self, message: discord.Message) -> bool:
        prefixes = set(self.all_prefixes) | set(self.bot_prefixes(message.guild.id).values())
        prefixes.add(self.bot.prefix.get(message.guild.id, self.bot.default_prefix))
        return any(prefix and message.content.startswith(prefix) for prefix in prefixes)

    async def _build_turn(self, message: discord.Message, text: str):
        '''Returns (content blocks for Claude, text-only version for history). Attachments are never read.'''
        name = message.author.display_name
        text = text.strip()
        if len(text) > MAX_INPUT_CHARS:
            text = text[:MAX_INPUT_CHARS] + ' …(message too long, cut off)'
        header = f'[{name}]: {text}'
        parts = [{'type': 'text', 'text': header}]
        notes = ''
        if message.attachments:
            notes += f' (also attached {len(message.attachments)} file(s), which you cannot see)'
            parts.append({'type': 'text', 'text': notes.strip()})
        reference = message.reference
        if reference and reference.message_id and reference.message_id not in self.message_to_conv:
            replied = reference.resolved if isinstance(reference.resolved, discord.Message) else None
            if replied is None:
                try:
                    replied = await message.channel.fetch_message(reference.message_id)
                except discord.HTTPException:
                    replied = None
            if replied is not None:
                quote = replied.clean_content[:800]
                notes += f'\n(replying to {replied.author.display_name}: {quote})'
                parts.append({'type': 'text', 'text': f'(replying to {replied.author.display_name}: {quote})'})
        return parts, header + notes

    async def _handle(self, message: discord.Message, conv_id: str, conv: Conversation, text: str = None):
        '''Run one user turn through the agent and send the reply'''
        text = message.clean_content if text is None else text
        sent = list()

        async def progress(update: str):
            for part in self.split_message(update):
                msg = await message.channel.send(part, allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False))
                self.message_to_conv[msg.id] = conv_id

        async with conv.lock:
            async with message.channel.typing():
                try:
                    parts, history_text = await self._build_turn(message, text)
                    context = ToolContext(bot=self.bot, cog=self, guild=message.guild, channel=message.channel,
                                          requester=message.author, message=message)
                    if self.client is None:
                        raise RuntimeError('ANTHROPIC_API_KEY is not configured')
                    result = await self.agent.run(conv, context, parts, history_text, on_progress=progress)
                except anthropic.APIStatusError as e:
                    error_text = str(e).lower()
                    if e.status_code == 402 or getattr(e, 'type', '') == 'billing_error' \
                            or 'credit balance' in error_text or 'usage limit' in error_text or 'spend' in error_text:
                        title, description = 'My AI budget is used up :money_with_wings:', \
                            "This month's AI budget (or the prepaid credit) is used up, so I can't think right now."
                        self.bot.log.error(f'GO-4 budget/billing error: {e}', message.guild)
                    elif e.status_code in (429, 529) or e.status_code >= 500:
                        title, description = 'My brain is busy :sweat_smile:', 'Claude is overloaded right now. Please try again in a minute.'
                        self.bot.log.warning(f'GO-4 API busy ({e.status_code}): {e}', message.guild)
                    else:
                        title, description = "I'm Sorry! :confused:", 'Something went wrong while generating a response. Please try again.'
                        self.bot.log.error(f'GO-4 API error ({e.status_code}) in {conv_id}: {e}', message.guild)
                    await message.reply(embed=discord.Embed(title=title, description=description,
                                                            color=self.bot.default_color), mention_author=False)
                    return
                except anthropic.APIConnectionError as e:
                    self.bot.log.warning(f'GO-4 could not reach the Claude API: {e}', message.guild)
                    await message.reply(embed=discord.Embed(title='My brain is unreachable :satellite:',
                                                            description='I could not reach Claude. Please try again in a minute.',
                                                            color=self.bot.default_color), mention_author=False)
                    return
                except Exception as e:
                    self.bot.log.error(f'GO-4 error in conversation {conv_id}: {type(e).__name__}: {e}', message.guild)
                    await message.reply(embed=discord.Embed(
                        title="I'm Sorry! :confused:",
                        description='Something went wrong while generating a response. Please try again.',
                        color=self.bot.default_color), mention_author=False)
                    return
            sent = await self._send_response(result.text, message)
        for msg in sent:
            self.message_to_conv[msg.id] = conv_id
        self._remember(conv_id, conv)
        try:
            self.record_usage(result)
        except Exception as e:
            self.bot.log.warning(f'GO-4 could not save usage: {e}', message.guild)
        tools = f" tools: {', '.join(result.tools_used)}" if result.tools_used else ''
        self.bot.log.info(f'GO-4 replied to @{message.author.name} in {conv_id} with {result.model}: '
                          f'{result.calls} calls, in {result.input_tokens} + cache write {result.cache_write_tokens} '
                          f'+ cache read {result.cache_read_tokens}, out {result.output_tokens} tokens.{tools}', message.guild)

    async def _send_response(self, response: str, reply_target: discord.Message) -> list:
        '''Split and send a response, returning all sent message objects'''
        mentions = discord.AllowedMentions(users=True, roles=False, everyone=False, replied_user=False)
        sent = list()
        for i, part in enumerate(self.split_message(response)):
            if i == 0:
                sent.append(await reply_target.reply(part, allowed_mentions=mentions, mention_author=False))
            else:
                sent.append(await reply_target.channel.send(part, allowed_mentions=mentions))
        return sent

    # ---- listeners ------------------------------------------------------------

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return
        if self._is_command(message):
            return
        content = message.content.strip()
        # Dedicated AI channel: every message is part of one shared conversation
        if self.ai_channels.get(message.guild.id) == message.channel.id:
            if content.lower() in RESET_WORDS:
                await self._reset_channel(message.channel, reply_to=message)
                return
            if not content:
                return
            conv_id, conv = self._channel_conv(message)
            await self._handle(message, conv_id, conv)
            return
        # Elsewhere: replying to one of GO-4's answers continues that conversation
        if message.reference and message.reference.message_id in self.message_to_conv:
            if not content:
                return
            conv_id = self.message_to_conv[message.reference.message_id]
            conv = self.conversations.get(conv_id)
            if conv is not None:
                await self._handle(message, conv_id, conv)

    async def _reset_channel(self, channel, reply_to=None):
        conv_id = f'channel-{channel.id}'
        self.conversations.pop(conv_id, None)
        self._forget_messages(conv_id)
        embed = discord.Embed(title='Fresh start :sparkles:', description='I forgot our previous conversation in this channel.',
                              color=self.bot.default_color)
        if reply_to is not None:
            await reply_to.reply(embed=embed, mention_author=False)
        else:
            await channel.send(embed=embed)

    # ---- commands -------------------------------------------------------------

    @commands.command(name='ask', description='Ask GO-4 anything. Reply to its answer to continue the conversation.', aliases=['a'])
    async def ask(self, context: Context, *, question: str):
        ''' Start a new conversation. Reply to GO-4's answer to continue it. '''
        conv_id = f"{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}-{context.author.name}"
        conv = Conversation(context.author.display_name, context.guild.id, context.channel.id, 'thread')
        self._remember(conv_id, conv)
        await self._handle(context.message, conv_id, conv, text=question)

    @ask.error
    async def ask_error(self, context: Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await context.reply(embed=discord.Embed(
                title='Missing Question',
                description=f'Usage: `{self.bot.prefix.get(context.guild.id, self.bot.default_prefix)}ask <your question>`',
                color=self.bot.default_color))

    @commands.command(name='set_ai_channel', description='Make a channel where everyone can talk to GO-4 without a prefix')
    @commands.has_permissions(manage_guild=True)
    async def set_ai_channel(self, context: Context, channel: discord.TextChannel = None):
        ''' Set the dedicated AI chat channel (default: this channel) '''
        channel = channel or context.channel
        self.ai_channels[context.guild.id] = channel.id
        self.bot.update_guild_yaml(context.guild.id, SETTINGS_FILE, lambda d: {**d, 'ai_channel': channel.id})
        await context.reply(embed=discord.Embed(
            title='AI channel set :robot:',
            description=f'Talk to me in {channel.mention} without any prefix. I can also ask the other bots to do things for you.\n'
                        f'Type `reset` there to start a fresh conversation.',
            color=self.bot.default_color))
        self.bot.log.info(f'AI channel set to #{channel.name}', context.guild)

    @commands.command(name='unset_ai_channel', description='Stop using the dedicated AI chat channel')
    @commands.has_permissions(manage_guild=True)
    async def unset_ai_channel(self, context: Context):
        ''' Remove the dedicated AI chat channel '''
        channel_id = self.ai_channels.pop(context.guild.id, None)
        self.bot.update_guild_yaml(context.guild.id, SETTINGS_FILE, lambda d: {k: v for k, v in d.items() if k != 'ai_channel'})
        if channel_id:
            self.conversations.pop(f'channel-{channel_id}', None)
            self._forget_messages(f'channel-{channel_id}')
        await context.reply(embed=discord.Embed(title='AI channel removed', color=self.bot.default_color,
                                                description='Use the ask command to talk to me.'))

    @commands.command(name='reset', description='Clear the conversation in the AI channel')
    async def reset(self, context: Context):
        ''' Clear the shared conversation of the AI channel '''
        await self._reset_channel(context.channel, reply_to=context.message)

    @commands.command(name='ai_usage', description="Show how many tokens GO-4's AI has used", aliases=['usage'])
    async def ai_usage(self, context: Context):
        ''' Monthly token usage of the AI assistant '''
        usage = self.bot.load_bot_yaml(USAGE_FILE)
        if not usage:
            await context.reply(embed=discord.Embed(title='AI usage', description='No AI usage recorded yet.',
                                                    color=self.bot.default_color))
            return
        lines = list()
        for month in sorted(usage, reverse=True)[:6]:
            row = usage[month]
            tokens_in = row['input_tokens'] + row['cache_write_tokens'] + row['cache_read_tokens']
            lines.append(f"**{month}**: {row['replies']} replies · {tokens_in:,} tokens in "
                         f"({row['cache_read_tokens']:,} from cache) · {row['output_tokens']:,} out")
        lines.append(f'\nModel: `{self.agent.model}` · see the Claude Console for the actual cost')
        await context.reply(embed=discord.Embed(title='AI usage', description='\n'.join(lines), color=self.bot.default_color))

    @commands.command(name='chats', description='List all tracked conversations')
    async def list_chats(self, context: Context):
        ''' List all active conversations in this server '''
        guild_convs = [(cid, conv) for cid, conv in self.conversations.items() if conv.guild_id == context.guild.id]
        if not guild_convs:
            await context.reply(embed=discord.Embed(title='No Conversations', color=self.bot.default_color,
                                                    description='There are no tracked conversations in this server.'))
            return
        lines = list()
        for i, (conv_id, conv) in enumerate(guild_convs, 1):
            started = conv.created_at.strftime('%Y-%m-%d %H:%M')
            where = f'AI channel <#{conv.channel_id}>' if conv.kind == 'channel' else f'**{conv.user}** in <#{conv.channel_id}>'
            lines.append(f'`{i}.` {where} · {started} · {conv.turns} turns')
        await context.reply(embed=discord.Embed(title=f'Conversations ({len(guild_convs)})',
                                                description='\n'.join(lines)[:4000], color=self.bot.default_color))

    @commands.command(name='clear_chat', description='Clear a conversation by its list number')
    async def clear_chat(self, context: Context, sl_no: int):
        ''' Clear a specific conversation (use the number from the chats list) '''
        conv_ids = [cid for cid, conv in self.conversations.items() if conv.guild_id == context.guild.id]
        if not 1 <= sl_no <= len(conv_ids):
            await context.reply(embed=discord.Embed(title='Invalid Number', color=self.bot.default_color,
                                                    description=f'Please give a number between 1 and {len(conv_ids)}.' if conv_ids else 'There are no conversations.'))
            return
        conv_id = conv_ids[sl_no - 1]
        self._forget_messages(conv_id)
        del self.conversations[conv_id]
        await context.reply(embed=discord.Embed(title='Conversation Cleared :wastebasket:', color=self.bot.default_color,
                                                description=f'Removed conversation {sl_no}.'))
        self.bot.log.info(f'Cleared conversation {conv_id}', context.guild)

    @commands.command(name='clear_all_chats', description='Clear all tracked conversations')
    @commands.is_owner()
    async def clear_all_chats(self, context: Context):
        ''' Clear all tracked conversations (owner only) '''
        count = len(self.conversations)
        self.conversations.clear()
        self.message_to_conv.clear()
        await context.reply(embed=discord.Embed(title='All Conversations Cleared :wastebasket:', color=self.bot.default_color,
                                                description=f'Removed {count} conversation(s).'))
        self.bot.log.info(f'Cleared all {count} conversations', context.guild)

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
                    parts.extend(textwrap.wrap(line, width=limit, break_long_words=True, break_on_hyphens=False))
                else:
                    current = line
            else:
                current = current + '\n' + line if current else line
        if current:
            parts.append(current)
        return parts or ['…']


async def setup(bot):
    await bot.add_cog(Assistant(bot))
