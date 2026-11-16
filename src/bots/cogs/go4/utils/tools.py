#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# Github: Kabilan-T

''' Tools GO-4's LLM can call: Discord info, actions, and other bots via the bridge '''

#-------------------------------------------------------------------------------

import re
import json
import asyncio
import itertools
import discord
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

MAX_TOOL_RESULT = 4000    # characters returned to the model per tool call (~1K tokens)
BOT_OUTPUT_MESSAGES = 3   # how many of the other bot's messages GO-4 gets back
BOT_OUTPUT_CHARS = 400    # characters kept per message (the full text is already in chat)


@dataclass
class ToolContext:
    bot: object
    cog: object               # the Assistant cog (triggers, bridge client, router, config)
    guild: discord.Guild
    channel: discord.abc.Messageable
    requester: discord.Member
    message: discord.Message  # the user's message that started this turn (None when a trigger fires)
    deferred: bool = False    # True when running for a trigger (nobody is watching)


class ToolError(Exception):
    pass


# ---- resolving names ---------------------------------------------------------

def resolve_channel(ctx: ToolContext, ref):
    '''Channel/thread by mention, id or name; defaults to the current channel'''
    if not ref:
        return ctx.channel
    ref = str(ref).strip()
    match = re.fullmatch(r'<#(\d+)>|(\d{15,25})', ref)
    if match:
        channel = ctx.guild.get_channel_or_thread(int(match.group(1) or match.group(2)))
        if channel:
            return channel
    name = ref.lstrip('#').strip().lower()
    candidates = list(ctx.guild.channels) + list(ctx.guild.threads)
    for channel in candidates:
        if channel.name.lower() == name:
            return channel
    for channel in candidates:
        if name and name in channel.name.lower():
            return channel
    raise ToolError(f'channel "{ref}" not found')


def resolve_member(ctx: ToolContext, ref):
    '''Member by mention, id, username or display name; defaults to the requester'''
    if not ref:
        return ctx.requester
    ref = str(ref).strip()
    match = re.fullmatch(r'<@!?(\d+)>|(\d{15,25})', ref)
    if match:
        member = ctx.guild.get_member(int(match.group(1) or match.group(2)))
        if member:
            return member
    name = ref.lstrip('@').strip().lower()
    for member in ctx.guild.members:
        if name in (member.name.lower(), member.display_name.lower(), (member.global_name or '').lower()):
            return member
    for member in ctx.guild.members:
        if name and (name in member.display_name.lower() or name in member.name.lower()):
            return member
    raise ToolError(f'member "{ref}" not found')


def require_send(ctx: ToolContext, channel):
    if not isinstance(channel, discord.abc.Messageable) or isinstance(channel, discord.CategoryChannel):
        raise ToolError(f'#{channel.name} is not a text channel')
    perms = channel.permissions_for(ctx.requester)
    if not (perms.view_channel and perms.send_messages):
        raise ToolError(f'{ctx.requester.display_name} cannot send messages in #{channel.name}')


def fmt_time(dt: datetime, tz) -> str:
    return dt.astimezone(tz).strftime('%Y-%m-%d %H:%M')


# ---- Discord info -----------------------------------------------------------

async def get_server_info(ctx):
    guild = ctx.guild
    humans = [m for m in guild.members if not m.bot]
    online = [m for m in humans if m.status != discord.Status.offline]
    visible_text = [c for c in guild.text_channels if c.permissions_for(ctx.requester).view_channel]
    voice = list()
    for vc in guild.voice_channels:
        if vc.permissions_for(ctx.requester).view_channel:
            people = ', '.join(m.display_name for m in vc.members) or 'empty'
            voice.append(f'{vc.name}: {people}')
    roles = [f'{r.name} ({len(r.members)})' for r in reversed(guild.roles) if not r.is_default()][:30]
    return {
        'name': guild.name,
        'owner': guild.owner.display_name if guild.owner else None,
        'created': fmt_time(guild.created_at, ctx.cog.tz),
        'members': guild.member_count, 'humans': len(humans), 'bots': guild.member_count - len(humans),
        'online_humans': ', '.join(m.display_name for m in online[:40]),
        'text_channels': ', '.join('#' + c.name for c in visible_text),
        'voice_channels': '\n'.join(voice),
        'roles': ', '.join(roles),
        'boost_level': guild.premium_tier,
    }


async def get_user_info(ctx, user=None):
    member = resolve_member(ctx, user)
    activity = None
    if member.activity:
        kind = getattr(member.activity, 'type', None)
        activity = f'{kind.name if kind else ""} {member.activity.name or ""}'.strip()
    return {
        'display_name': member.display_name, 'username': member.name, 'id': str(member.id),
        'is_bot': member.bot,
        'status': str(member.status), 'activity': activity,
        'joined_server': fmt_time(member.joined_at, ctx.cog.tz) if member.joined_at else None,
        'account_created': fmt_time(member.created_at, ctx.cog.tz),
        'roles': ', '.join(r.name for r in reversed(member.roles) if not r.is_default()),
        'in_voice': member.voice.channel.name if member.voice and member.voice.channel else None,
        'timed_out_until': fmt_time(member.timed_out_until, ctx.cog.tz) if member.is_timed_out() else None,
        'avatar': member.display_avatar.url,
        'mention': member.mention,
    }


# ---- Actions -------------------------------------------------------------------

def allowed_mentions_for(ctx, channel):
    perms = channel.permissions_for(ctx.requester)
    return discord.AllowedMentions(everyone=perms.mention_everyone, roles=perms.mention_everyone,
                                   users=True, replied_user=False)


async def create_poll(ctx, question, options, duration_hours=24, allow_multiple=False, channel=None):
    target = resolve_channel(ctx, channel)
    require_send(ctx, target)
    options = [str(o).strip() for o in (options or []) if str(o).strip()]
    if not 2 <= len(options) <= 10:
        raise ToolError('a poll needs between 2 and 10 options')
    hours = max(1, min(int(duration_hours or 24), 32 * 24))
    poll = discord.Poll(question=str(question)[:300], duration=timedelta(hours=hours), multiple=bool(allow_multiple))
    for option in options:
        poll.add_answer(text=option[:55])
    message = await target.send(f'📊 Poll for {ctx.requester.mention}', poll=poll,
                                allowed_mentions=discord.AllowedMentions.none())
    return {'created': True, 'channel': f'#{target.name}', 'link': message.jump_url, 'ends_in_hours': hours}


TZ_ALIASES = {
    'UTC': 'UTC', 'GMT': 'UTC', 'Z': 'UTC',
    'IST': 'Asia/Kolkata', 'INDIA': 'Asia/Kolkata',
    'CET': 'Europe/Berlin', 'CEST': 'Europe/Berlin', 'BERLIN': 'Europe/Berlin', 'GERMANY': 'Europe/Berlin',
    'BST': 'Europe/London', 'UK': 'Europe/London', 'LONDON': 'Europe/London',
    'EST': 'America/New_York', 'EDT': 'America/New_York', 'ET': 'America/New_York',
    'CST': 'America/Chicago', 'CDT': 'America/Chicago', 'CT': 'America/Chicago',
    'MST': 'America/Denver', 'MDT': 'America/Denver', 'MT': 'America/Denver',
    'PST': 'America/Los_Angeles', 'PDT': 'America/Los_Angeles', 'PT': 'America/Los_Angeles',
}


def resolve_timezone(name):
    '''Time zone from an abbreviation (IST, EST, ...) or IANA name (Asia/Kolkata); default UTC'''
    if not name:
        return ZoneInfo('UTC')
    key = str(name).strip()
    key = TZ_ALIASES.get(key.upper().replace(' TIME', ''), key)
    try:
        return ZoneInfo(key)
    except (ZoneInfoNotFoundError, ValueError):
        raise ToolError(f'unknown time zone "{name}"; use e.g. UTC, IST, CET, EST, PST or a name like Asia/Kolkata')


def discord_time(when: datetime) -> str:
    '''Discord timestamp tags: every reader sees the time in their own time zone'''
    ts = int(when.timestamp())
    return f'<t:{ts}:f> (<t:{ts}:R>)'


def _parse_when(in_minutes, at_time, tz_name):
    now = datetime.now(timezone.utc)
    if in_minutes is not None:
        return now + timedelta(minutes=float(in_minutes))
    if at_time:
        tz = resolve_timezone(tz_name)
        text = str(at_time).strip().replace('T', ' ')
        for fmt in ('%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S', '%H:%M'):
            try:
                parsed = datetime.strptime(text, fmt)
            except ValueError:
                continue
            local_now = now.astimezone(tz)
            if fmt == '%H:%M':
                parsed = local_now.replace(hour=parsed.hour, minute=parsed.minute, second=0, microsecond=0)
                if parsed <= local_now:
                    parsed += timedelta(days=1)
                return parsed.astimezone(timezone.utc)
            return parsed.replace(tzinfo=tz).astimezone(timezone.utc)
        try:
            parsed = datetime.fromisoformat(text)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=tz)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            pass
        raise ToolError('could not understand the time; use "YYYY-MM-DD HH:MM" or "HH:MM"')
    raise ToolError('give either in_minutes or at_time')


# ---- Triggers: do something later (timer) or when something happens (event) ----

TRIGGER_EVENTS = ('time', 'online', 'joins_voice', 'leaves_voice', 'joins_server')
TRIGGER_TOOLS = ('send_message', 'run_bot_command', 'create_poll')  # allowed fixed actions
MAX_TRIGGERS = 20             # pending triggers per server
MAX_TRIGGER_DAYS = 7          # how far ahead a timer / how long an event trigger may wait
DEFAULT_EVENT_HOURS = 24      # event triggers expire after this unless told otherwise
# Never run unattended (by a trigger): moderation, and Cosmic Con commands that ban/kick
DEFERRED_BLOCKED_COMMANDS = {
    'mute', 'unmute', 'deafen', 'undeafen', 'timeout', 'remove_timeout', 'warn', 'remove_warn', 'clear_warns',
    'kick', 'softban', 'ban', 'unban', 'purge', 'purge_user',
    'order66', 'thanos_snap', 'redpill_or_bluepill', 'horcrux',
}
_trigger_ids = itertools.count(1)


def check_deferred_command(command: str):
    name = str(command).strip().split(' ', 1)[0].lower()
    if name in DEFERRED_BLOCKED_COMMANDS:
        raise ToolError(f'"{name}" is a moderation command and cannot be run by a trigger')


def _cut(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit] + '…'


def trigger_event_text(t: dict) -> str:
    '''Human description of when a trigger fires'''
    who = t.get('user_name') or 'anyone'
    where = f" '{t['voice_channel_name']}'" if t.get('voice_channel_name') else ''
    return {
        'time': f"at {fmt_time(t['deadline'], timezone.utc)} UTC",
        'online': f'when {who} comes online',
        'joins_voice': f'when {who} joins voice{where}',
        'leaves_voice': f'when {who} leaves voice{where}',
        'joins_server': 'when a new member joins the server',
    }[t['event']]


def trigger_action_text(t: dict) -> str:
    if t.get('instruction'):
        return 'decide then: ' + _cut(t['instruction'], 150)
    return f"{t['tool']} {_cut(json.dumps(t['tool_args'], ensure_ascii=False), 150)}"


async def set_trigger(ctx, event, instruction=None, tool=None, tool_args=None, user=None, voice_channel=None,
                      in_minutes=None, at_time=None, timezone_name=None, expires_in_hours=None):
    if ctx.deferred:
        raise ToolError('a trigger cannot create new triggers')
    event = str(event).strip().lower()
    if event not in TRIGGER_EVENTS:
        raise ToolError(f'unknown event "{event}"; use one of: {", ".join(TRIGGER_EVENTS)}')
    if bool(instruction) == bool(tool):
        raise ToolError('give either tool + tool_args (fixed action) or instruction (decided when it fires), not both')
    if tool:
        if tool not in TRIGGER_TOOLS:
            raise ToolError(f'tool must be one of: {", ".join(TRIGGER_TOOLS)}')
        if not isinstance(tool_args, dict):
            raise ToolError('tool_args must be an object with the arguments of that tool')
        if tool == 'run_bot_command':
            check_deferred_command(tool_args.get('command', ''))
    triggers = ctx.cog.triggers
    if sum(1 for t in triggers.values() if t['guild_id'] == ctx.guild.id) >= MAX_TRIGGERS:
        raise ToolError(f'too many pending triggers in this server (max {MAX_TRIGGERS})')

    now = datetime.now(timezone.utc)
    member, voice = None, None
    if event == 'time':
        deadline = _parse_when(in_minutes, at_time, timezone_name)
        if (deadline - now).total_seconds() < 5:
            raise ToolError('that time is in the past')
    else:
        hours = float(expires_in_hours or DEFAULT_EVENT_HOURS)
        deadline = now + timedelta(hours=max(0.1, hours))
        if event == 'online' or user:
            member = resolve_member(ctx, user)  # 'online' without a user means the person asking
        if voice_channel and event in ('joins_voice', 'leaves_voice'):
            voice = resolve_channel(ctx, voice_channel)
            if not isinstance(voice, (discord.VoiceChannel, discord.StageChannel)):
                raise ToolError(f'#{voice.name} is not a voice channel')
    if deadline - now > timedelta(days=MAX_TRIGGER_DAYS):
        raise ToolError(f'triggers can wait at most {MAX_TRIGGER_DAYS} days')

    trigger_id = next(_trigger_ids)
    trigger = {
        'id': trigger_id, 'guild_id': ctx.guild.id, 'channel_id': ctx.channel.id, 'channel_name': ctx.channel.name,
        'creator_id': ctx.requester.id, 'creator_name': ctx.requester.display_name,
        'event': event, 'deadline': deadline,
        'user_id': member.id if member else None, 'user_name': member.display_name if member else None,
        'voice_channel_id': voice.id if voice else None, 'voice_channel_name': voice.name if voice else None,
        'tool': tool, 'tool_args': dict(tool_args) if tool else None, 'instruction': instruction,
    }
    triggers[trigger_id] = trigger
    trigger['task'] = asyncio.create_task(ctx.cog.trigger_timer(trigger_id))

    result = {'id': trigger_id, 'fires': trigger_event_text(trigger), 'action': trigger_action_text(trigger),
              'note': 'fires once; kept in memory, lost if GO-4 restarts'}
    if event == 'time':
        result['discord_time'] = discord_time(deadline)
    else:
        result['expires'] = discord_time(deadline)
        if event == 'online' and member.status != discord.Status.offline:
            result['warning'] = f'{member.display_name} is already online; it fires the next time they come online'
        if event == 'joins_voice' and member and member.voice and member.voice.channel:
            result['warning'] = f'{member.display_name} is already in voice ({member.voice.channel.name})'
    return result


async def list_triggers(ctx):
    rows = [f"#{tid}: {trigger_event_text(t)} → {trigger_action_text(t)} (by {t['creator_name']}, in #{t['channel_name']})"
            + ('' if t['event'] == 'time' else f", expires {discord_time(t['deadline'])}")
            for tid, t in sorted(ctx.cog.triggers.items()) if t['guild_id'] == ctx.guild.id]
    return {'triggers': '\n'.join(rows) or 'no pending triggers'}


async def cancel_trigger(ctx, trigger_id):
    trigger = ctx.cog.triggers.get(int(trigger_id))
    if trigger is None or trigger['guild_id'] != ctx.guild.id:
        raise ToolError(f'no trigger #{trigger_id}')
    if trigger['creator_id'] != ctx.requester.id and not ctx.requester.guild_permissions.manage_messages:
        raise ToolError('only the person who set it (or a moderator) can cancel it')
    ctx.cog.triggers.pop(int(trigger_id), None)
    trigger['task'].cancel()
    return {'cancelled': int(trigger_id)}


async def send_message(ctx, channel, text, title=None):
    target = resolve_channel(ctx, channel)
    require_send(ctx, target)
    mentions = allowed_mentions_for(ctx, target)
    if title:
        embed = discord.Embed(title=str(title)[:256], description=str(text)[:4000], color=ctx.bot.default_color)
        embed.set_footer(text=f'Requested by {ctx.requester.display_name}')
        message = await target.send(embed=embed, allowed_mentions=mentions)
    else:
        message = await target.send(str(text)[:2000], allowed_mentions=mentions)
    return {'sent': True, 'channel': f'#{target.name}', 'link': message.jump_url}


# ---- Other bots (bridge) -------------------------------------------------------

def _resolve_bot(ctx, name):
    key = re.sub(r'[^a-z0-9]', '', str(name).lower())
    for bot_key, info in ctx.cog.bridge_bots.items():
        if key in (bot_key, re.sub(r'[^a-z0-9]', '', info['name'].lower())):
            return bot_key, info
    raise ToolError(f'unknown bot "{name}". Available: ' + ', '.join(i['name'] for i in ctx.cog.bridge_bots.values()))


async def run_bot_command(ctx, bot, command):
    bot_key, info = _resolve_bot(ctx, bot)
    prefix = ctx.cog.bot_prefixes(ctx.guild.id).get(bot_key, info['prefix'])
    command = str(command).strip()
    if ctx.deferred:
        check_deferred_command(command)
    for p in (prefix, info['prefix']):
        if p and command.startswith(p):
            command = command[len(p):]
            break
    if not command:
        raise ToolError('empty command')
    shown = command if len(command) <= 300 else command[:300] + '…'
    handoff = await ctx.channel.send(
        f"🛰️ **{info['name']}** ← `{prefix}{shown}` · for {ctx.requester.display_name}",
        allowed_mentions=discord.AllowedMentions.none())
    try:
        result = await ctx.cog.bridge_call(info, 'POST', '/run', json={
            'guild_id': str(ctx.guild.id), 'channel_id': str(ctx.channel.id),
            'message_id': str(handoff.id), 'requester_id': str(ctx.requester.id), 'command': command,
        })
    except ToolError:
        await _react(handoff, '⚠️')
        raise
    await _react(handoff, '✅' if result.get('ok') else '❌')
    return {'bot': info['name'], 'ok': result.get('ok'), 'error': result.get('error'),
            'usage': result.get('usage'),
            'bot_output_already_shown_in_chat': [text[:BOT_OUTPUT_CHARS] for text in result.get('bot_output', [])[-BOT_OUTPUT_MESSAGES:]]}


async def _react(message, emoji):
    try:
        await message.add_reaction(emoji)
    except discord.HTTPException:
        pass


# ---- Registry ----------------------------------------------------------------

def _schema(properties: dict, required: list = None):
    return {'type': 'object', 'properties': properties, 'required': required or []}


_STR = {'type': 'string'}
_INT = {'type': 'integer'}

TOOLS = {
    'get_server_info': (get_server_info,
        'Get information about this Discord server: members, who is online, channels, who is in which voice channel, roles.',
        _schema({})),
    'get_user_info': (get_user_info,
        'Get information about a server member: roles, join date, status, activity, voice channel, avatar.',
        _schema({'user': {**_STR, 'description': 'name, mention or id; omit for the person asking'}})),
    'create_poll': (create_poll,
        'Create a native Discord poll.',
        _schema({'question': _STR,
                 'options': {'type': 'array', 'items': _STR, 'description': '2-10 answer options'},
                 'duration_hours': {**_INT, 'description': 'how long the poll runs (default 24)'},
                 'allow_multiple': {'type': 'boolean', 'description': 'allow choosing several answers'},
                 'channel': {**_STR, 'description': 'channel name; omit for current channel'}},
                ['question', 'options'])),
    'set_trigger': (set_trigger,
        'Do something later or when something happens; fires once. Use it for reminders too. Event "time" needs in_minutes '
        'or at_time; the other events wait up to expires_in_hours. Action: EITHER tool + tool_args when everything is known now '
        '(e.g. reminder = send_message tagging the person; "{member}" in a text is replaced by the member who caused the event), '
        'OR instruction when it depends on the situation then (you get it back, with your tools, when it fires). '
        'Moderation commands are not allowed.',
        _schema({'event': {'type': 'string', 'enum': list(TRIGGER_EVENTS)},
                 'in_minutes': {'type': 'number', 'description': 'time: minutes from now'},
                 'at_time': {**_STR, 'description': 'time: clock time "YYYY-MM-DD HH:MM" or "HH:MM" (next occurrence)'},
                 'timezone_name': {**_STR, 'description': 'time zone of at_time if the user named one: IST, CET, EST, PST, or e.g. Asia/Kolkata. Omit for UTC'},
                 'user': {**_STR, 'description': 'online/voice events: whose event (online defaults to the person asking; voice: omit for anyone)'},
                 'voice_channel': {**_STR, 'description': 'voice events: only this voice channel'},
                 'expires_in_hours': {'type': 'number', 'description': f'events: give up after this long (default {DEFAULT_EVENT_HOURS})'},
                 'tool': {'type': 'string', 'enum': list(TRIGGER_TOOLS), 'description': 'fixed action: the tool to call'},
                 'tool_args': {'type': 'object', 'description': 'fixed action: that tool\'s arguments, e.g. {"channel": "general", "text": "..."}'},
                 'instruction': {**_STR, 'description': 'flexible action: what to do when it fires, in plain words with names'}},
                ['event'])),
    'list_triggers': (list_triggers, 'List pending triggers in this server.', _schema({})),
    'cancel_trigger': (cancel_trigger, 'Cancel a pending trigger by its id.',
        _schema({'trigger_id': _INT}, ['trigger_id'])),
    'send_message': (send_message,
        'Post a message in a channel (as GO-4). With a title it is sent as an embed (good for announcements).',
        _schema({'channel': _STR, 'text': _STR, 'title': {**_STR, 'description': 'optional embed title'}},
                ['channel', 'text'])),
    'run_bot_command': (run_bot_command,
        "Ask a bot (another bot or GO-4 itself) to run one of its commands (listed in your instructions) for the user, visibly in this "
        "channel. Runs with the user's own permissions. Give the command without prefix, e.g. 'play mirchi_fm'. "
        "The bot's reply is already shown in chat; you get a copy to check success.",
        _schema({'bot': {**_STR, 'description': 'bot name, e.g. AUTO, EVE, M-O, GO-4'},
                 'command': {**_STR, 'description': 'command name and arguments, without prefix'}},
                ['bot', 'command'])),
}


def tool_definitions() -> list:
    '''Tool definitions in Claude API format (stable order keeps the prompt cache valid)'''
    return [{'name': name, 'description': desc, 'input_schema': schema}
            for name, (_, desc, schema) in TOOLS.items()]


async def call_tool(ctx: ToolContext, name: str, args: dict):
    '''Run a tool; always returns a dict (errors included) sized for the model'''
    if name not in TOOLS:
        return {'error': f'unknown tool {name}'}
    handler = TOOLS[name][0]
    try:
        result = await handler(ctx, **(args or {}))
    except ToolError as e:
        return {'error': str(e)}
    except TypeError as e:
        return {'error': f'bad arguments: {e}'}
    except discord.Forbidden:
        return {'error': 'GO-4 is missing Discord permissions for that'}
    except Exception as e:
        ctx.bot.log.warning(f'Tool {name} failed: {type(e).__name__}: {e}', ctx.guild)
        return {'error': f'{type(e).__name__}: {e}'}
    text = str(result)
    if len(text) > MAX_TOOL_RESULT:
        result = {'truncated': True, 'data': text[:MAX_TOOL_RESULT]}
    return result
