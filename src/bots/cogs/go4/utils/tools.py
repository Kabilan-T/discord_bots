#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# Github: Kabilan-T

''' Tools GO-4's LLM can call: Discord info, actions, and other bots via the bridge '''

#-------------------------------------------------------------------------------

import re
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
    cog: object               # the Assistant cog (reminders, bridge client, router, config)
    guild: discord.Guild
    channel: discord.abc.Messageable
    requester: discord.Member
    message: discord.Message  # the user's message that started this turn


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


_reminder_ids = itertools.count(1)


async def set_reminder(ctx, text, in_minutes=None, at_time=None, timezone_name=None, for_user=None, channel=None):
    target = resolve_channel(ctx, channel)
    require_send(ctx, target)
    member = resolve_member(ctx, for_user)
    when = _parse_when(in_minutes, at_time, timezone_name)
    delay = (when - datetime.now(timezone.utc)).total_seconds()
    if delay < 5:
        raise ToolError('that time is in the past')
    if delay > 30 * 86400:
        raise ToolError('reminders can be at most 30 days ahead')
    reminders = ctx.cog.reminders
    if sum(1 for r in reminders.values() if r['guild_id'] == ctx.guild.id) >= 50:
        raise ToolError('too many reminders in this server (max 50)')
    reminder_id = next(_reminder_ids)
    by = ctx.requester.display_name
    requester_id = ctx.requester.id
    log, guild = ctx.bot.log, ctx.guild

    async def fire():
        try:
            await asyncio.sleep(delay)
            note = f'⏰ {member.mention} reminder' + (f' (from {by})' if member.id != requester_id else '') + f': {text}'
            await target.send(note, allowed_mentions=discord.AllowedMentions(users=True, roles=False, everyone=False))
        except asyncio.CancelledError:
            raise
        except Exception as e:
            log.warning(f'Reminder {reminder_id} failed: {e}', guild)
        finally:
            reminders.pop(reminder_id, None)

    reminders[reminder_id] = {
        'task': asyncio.create_task(fire()), 'guild_id': ctx.guild.id, 'creator_id': requester_id,
        'for': member.display_name, 'text': text, 'when': when, 'channel': target.name,
    }
    return {'id': reminder_id, 'for': member.display_name, 'at_utc': fmt_time(when, timezone.utc) + ' UTC',
            'discord_time': discord_time(when), 'channel': f'#{target.name}',
            'note': 'reminders are kept in memory and are lost if the bot restarts'}


async def list_reminders(ctx):
    rows = [f"#{rid}: for {r['for']} at {fmt_time(r['when'], timezone.utc)} UTC {discord_time(r['when'])} in #{r['channel']}: {r['text']}"
            for rid, r in sorted(ctx.cog.reminders.items()) if r['guild_id'] == ctx.guild.id]
    return {'reminders': '\n'.join(rows) or 'no pending reminders'}


async def cancel_reminder(ctx, reminder_id):
    reminder = ctx.cog.reminders.get(int(reminder_id))
    if reminder is None or reminder['guild_id'] != ctx.guild.id:
        raise ToolError(f'no reminder #{reminder_id}')
    if reminder['creator_id'] != ctx.requester.id and not ctx.requester.guild_permissions.manage_messages:
        raise ToolError('only the person who set it (or a moderator) can cancel it')
    reminder['task'].cancel()
    ctx.cog.reminders.pop(int(reminder_id), None)
    return {'cancelled': int(reminder_id)}


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
    'set_reminder': (set_reminder,
        'Set a reminder that pings a user later in a channel. Give either in_minutes or at_time.',
        _schema({'text': {**_STR, 'description': 'what to remind about'},
                 'in_minutes': {'type': 'number', 'description': 'minutes from now (for relative times like "in 2 hours")'},
                 'at_time': {**_STR, 'description': 'clock time "YYYY-MM-DD HH:MM" or "HH:MM" (next occurrence)'},
                 'timezone_name': {**_STR, 'description': 'time zone of at_time if the user named one: IST, CET, EST, PST, GMT, or e.g. Asia/Kolkata. Omit for UTC'},
                 'for_user': {**_STR, 'description': 'who to ping; omit for the person asking'},
                 'channel': {**_STR, 'description': 'channel name; omit for current channel'}},
                ['text'])),
    'list_reminders': (list_reminders, 'List pending reminders in this server.', _schema({})),
    'cancel_reminder': (cancel_reminder, 'Cancel a pending reminder by its id.',
        _schema({'reminder_id': _INT}, ['reminder_id'])),
    'send_message': (send_message,
        'Post a message in a channel (as GO-4). With a title it is sent as an embed (good for announcements).',
        _schema({'channel': _STR, 'text': _STR, 'title': {**_STR, 'description': 'optional embed title'}},
                ['channel', 'text'])),
    'run_bot_command': (run_bot_command,
        "Ask another bot to run one of its commands (listed in your instructions) for the user, visibly in this "
        "channel. Runs with the user's own permissions. Give the command without prefix, e.g. 'play mirchi_fm'. "
        "The bot's reply is already shown in chat; you get a copy to check success.",
        _schema({'bot': {**_STR, 'description': 'bot name, e.g. AUTO, EVE, M-O'},
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
