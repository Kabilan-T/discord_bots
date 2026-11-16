#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# Github: Kabilan-T

''' GO-4 agent on Claude: system prompt, tool-calling loop, conversation history, token tracking '''

#-------------------------------------------------------------------------------

import json
import asyncio
from datetime import datetime
from dataclasses import dataclass, field
from .tools import call_tool, tool_definitions, ToolContext


class Conversation:
    '''In-memory conversation (cleared when the bot restarts)'''
    def __init__(self, user: str, guild_id: int, channel_id: int, kind: str):
        self.user = user
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.kind = kind            # 'thread' (started with ask) or 'channel' (dedicated AI channel)
        self.history = list()       # [{'role', 'content': str}] text only: user turns and final answers
        self.lock = asyncio.Lock()
        self.created_at = datetime.now()
        self.turns = 0


@dataclass
class AgentResult:
    text: str
    model: str = None
    tools_used: list = field(default_factory=list)
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_write_tokens: int = 0
    cache_read_tokens: int = 0


def _short(value, limit) -> str:
    text = json.dumps(value, ensure_ascii=False, default=str)
    return text if len(text) <= limit else text[:limit] + '…'


HISTORY_USER_CHARS = 600    # each remembered user message is shortened to this (a pasted wall of text stays small)
HISTORY_REPLY_CHARS = 1000  # each remembered GO-4 reply is shortened to this


def _approx_tokens(history) -> int:
    '''~4 English characters per token; non-Latin letters (Tamil etc.) count about 1 token each'''
    total = 0
    for message in history:
        text = message['content']
        ascii_chars = sum(1 for ch in text if ord(ch) < 128)
        total += ascii_chars // 4 + (len(text) - ascii_chars)
    return total


def _clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit] + ' …(shortened)'


STABLE_PROMPT = '''You are GO-4, the AI assistant of a Discord server. You chat with the members and coordinate the server's other bots.

Style:
- Friendly, natural and concise. Aim for under 800 characters unless asked for detail. Use Discord markdown sparingly.
- Reply in the language the user writes in (Tamil, Tanglish, English, German, ...).
- User messages start with the sender's name like "[Name]: ...". Several people may talk in one conversation. Never prefix your own reply with a name.

Tools (use them instead of guessing, but only when needed):
- Discord: get_server_info, get_user_info.
- Actions: create_poll, set_reminder / list_reminders / cancel_reminder, send_message.
- Other bots: run_bot_command with a command from the list in the live context. It runs with the requesting user's permissions and the bot answers visibly in the chat, so do not repeat its output: confirm briefly, or explain a failure and fix it (e.g. unknown radio station: list the stations, then retry). Chain several commands when needed.
- Voice: you have no voice of your own. To say something aloud, ask EVE (say <text>). M-O plays radio. Voice commands need the user to be in a voice channel (see live context); bots join it automatically.
- You already know the voice status and the bot commands from the live context, so do not look them up with other tools.
- The earlier messages of this conversation are already above. You cannot read other channel messages.

Times (members live in Europe, India and the US):
- A clock time without a time zone means UTC. If the user names one (IST, CET, EST, PST, "India time", ...), pass it as timezone_name. Relative times ("in 2 hours") use in_minutes.
- When you confirm a reminder or mention a specific time, give it in UTC and add the discord_time tag from the tool result exactly as returned (Discord shows it in each reader's own time zone), so people can spot a wrong zone and correct you.

Rules:
- Only take actions (polls, reminders, posting messages, bot commands) when the user asks for them. Ask before moderation actions (timeout, ban, kick, warn, mute, purge) unless the request is explicit and unambiguous.
- Never invent commands, channel names or facts. You cannot browse the web or open links; if asked about current events, say your knowledge may be out of date. If a tool returns an error, explain it simply and do not call it again for the same purpose.'''


class Agent:
    def __init__(self, client, model: str, tz, effort: str = 'low', max_tokens: int = 2048,
                 max_steps: int = 6, max_turns: int = 20, max_history_tokens: int = 20000, log=None):
        self.client = client
        self.model = model
        self.tz = tz
        self.effort = effort
        self.max_tokens = max_tokens
        self.max_steps = max_steps
        self.max_turns = max_turns
        self.max_history_tokens = max_history_tokens
        self.log = log
        self.tools = tool_definitions()

    def _system(self, ctx: ToolContext, live_context: str) -> list:
        '''Stable part first (cached across turns), then the per-turn facts'''
        now = datetime.now(self.tz)
        live = (f'Server: "{ctx.guild.name}". Channel: #{getattr(ctx.channel, "name", "?")}. '
                f'Now: {now:%A %Y-%m-%d %H:%M} UTC (<t:{int(now.timestamp())}:f>).\n'
                f'{live_context}')
        return [
            {'type': 'text', 'text': STABLE_PROMPT, 'cache_control': {'type': 'ephemeral'}},
            {'type': 'text', 'text': 'Live context:\n' + live},
        ]

    async def run(self, conv: Conversation, ctx: ToolContext, user_content: list, history_text: str,
                  on_progress=None) -> AgentResult:
        '''
        user_content: content blocks for this turn (text + images/files)
        history_text: text-only version of the turn that is kept in history
        on_progress:  async callback(text) for text Claude says while calling tools
        '''
        try:
            live = await ctx.cog.live_context(ctx.guild, ctx.requester)
        except Exception as e:
            live = f'(live context unavailable: {e})'
        system = self._system(ctx, live)
        # Within a turn the messages are append-only (thinking blocks are passed back unchanged)
        messages = list(conv.history) + [{'role': 'user', 'content': user_content}]
        result = AgentResult(text='', model=self.model)
        actions = list()

        for step in range(self.max_steps + 1):
            last = step == self.max_steps
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system,
                tools=self.tools,
                tool_choice={'type': 'none'} if last else {'type': 'auto'},
                output_config={'effort': self.effort},
                cache_control={'type': 'ephemeral'},  # caches the growing prefix between tool steps
                messages=messages,
            )
            usage = response.usage
            result.calls += 1
            result.input_tokens += usage.input_tokens or 0
            result.output_tokens += usage.output_tokens or 0
            result.cache_write_tokens += usage.cache_creation_input_tokens or 0
            result.cache_read_tokens += usage.cache_read_input_tokens or 0

            text = ''.join(block.text for block in response.content if block.type == 'text').strip()
            tool_uses = [block for block in response.content if block.type == 'tool_use']
            if response.stop_reason == 'refusal':
                result.text = "Sorry, I can't help with that."
                break
            if response.stop_reason != 'tool_use' or not tool_uses:
                result.text = text
                break

            messages.append({'role': 'assistant', 'content': response.content})
            if text and on_progress:
                await on_progress(text)
            tool_results = list()
            for tool_use in tool_uses:
                output = await call_tool(ctx, tool_use.name, tool_use.input)
                is_error = isinstance(output, dict) and bool(output.get('error'))
                actions.append(f"{tool_use.name}({_short(tool_use.input, 150)}) → "
                               + ('error: ' + str(output.get('error'))[:100] if is_error else 'ok'))
                if self.log:
                    self.log.info(f'GO-4 tool {tool_use.name} {_short(tool_use.input, 200)} -> {_short(output, 300)}', ctx.guild)
                tool_results.append({'type': 'tool_result', 'tool_use_id': tool_use.id,
                                     'content': json.dumps(output, ensure_ascii=False, default=str),
                                     'is_error': is_error})
            messages.append({'role': 'user', 'content': tool_results})

        if not result.text:
            result.text = '✅ Done.' if actions else "Hmm, I couldn't come up with a reply. Try rephrasing?"

        # Keep only text in history: the user's turn, and the answer + a short note of actions taken
        remembered = result.text + (('\n[actions: ' + '; '.join(actions) + ']') if actions else '')
        conv.history += [{'role': 'user', 'content': _clip(history_text, HISTORY_USER_CHARS)},
                         {'role': 'assistant', 'content': _clip(remembered, HISTORY_REPLY_CHARS)}]
        conv.history = conv.history[-2 * self.max_turns:]
        while len(conv.history) > 2 and _approx_tokens(conv.history) > self.max_history_tokens:
            conv.history = conv.history[2:]
        conv.turns += 1

        result.tools_used = [a.split('(')[0] for a in actions]
        return result
