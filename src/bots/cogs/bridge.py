#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Local bridge: lets GO-4 list and run this bot's commands on behalf of a user '''

#-------------------------------------------------------------------------------

import os
import copy
import hmac
import yaml
import asyncio
import secrets
import discord
from aiohttp import web
from discord.ext import commands
from bots.base import config_file, data as DATA_ROOT

BRIDGE_HOST = '127.0.0.1'
SECRET_PATH = os.path.join(DATA_ROOT, 'bridge', 'secret')
DEFAULT_BLOCKED_COGS = ['Manage', 'Developer Control', 'General']
COMMAND_TIMEOUT = 60      # seconds a bridged command may run
OUTPUT_GRACE = 1.5        # seconds to keep collecting the bot's messages after the command returns


def load_full_config() -> dict:
    '''Load the whole config.yml (all bots + bridge settings)'''
    with open(config_file, 'r') as file:
        return yaml.safe_load(file) or dict()


def load_bridge_registry() -> dict:
    '''{bot_key: {name, prefix, port, about}} for every bot that exposes a bridge'''
    registry = dict()
    for key, conf in load_full_config().items():
        if isinstance(conf, dict) and conf.get('bridge_port'):
            registry[key] = {
                'name': conf.get('name', key),
                'prefix': conf.get('default_prefix', ''),
                'port': int(conf['bridge_port']),
                'about': conf.get('bridge_about', ''),
                'client_id': conf.get('client_id'),
            }
    return registry


def get_guild_prefix(bot_key: str, guild_id: int) -> str:
    '''A bot's prefix in a guild, read from that bot's settings.yml (same machine)'''
    conf = load_full_config().get(bot_key, {}) or {}
    path = os.path.join(DATA_ROOT, conf.get('name', bot_key), 'guilds', str(guild_id), 'settings.yml')
    try:
        with open(path, 'r') as file:
            settings = yaml.safe_load(file) or dict()
        return settings.get('prefix') or conf.get('default_prefix', '')
    except (OSError, yaml.YAMLError):
        return conf.get('default_prefix', '')


def get_bridge_secret() -> str:
    '''Shared secret for all local bots; created on first use, readable only by this user'''
    os.makedirs(os.path.dirname(SECRET_PATH), exist_ok=True)
    try:
        fd = os.open(SECRET_PATH, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as file:
            file.write(secrets.token_hex(32))
    except FileExistsError:
        pass
    for _ in range(10):  # another bot may be writing it right now
        with open(SECRET_PATH, 'r') as file:
            secret = file.read().strip()
        if secret:
            return secret
        import time; time.sleep(0.1)
    raise RuntimeError('Bridge secret file is empty')


def summarize_message(message: discord.Message, limit: int = 700) -> str:
    '''Compact text version of a message (content + embeds + attachments)'''
    parts = list()
    if message.content:
        parts.append(message.content)
    for embed in message.embeds:
        if embed.title:
            parts.append(f'[{embed.title}]')
        if embed.description:
            parts.append(embed.description)
        for field in embed.fields:
            parts.append(f'{field.name}: {field.value}')
    for attachment in message.attachments:
        parts.append(f'(attachment: {attachment.filename})')
    text = '\n'.join(parts)
    return text if len(text) <= limit else text[:limit] + ' …'


def describe_error(error: Exception, usage: str) -> str:
    '''Human readable reason for a failed command'''
    if isinstance(error, commands.MissingPermissions):
        return f"the requesting user lacks permissions: {', '.join(error.missing_permissions)}"
    if isinstance(error, commands.BotMissingPermissions):
        return f"the bot lacks permissions: {', '.join(error.missing_permissions)}"
    if isinstance(error, (commands.MissingRole, commands.MissingAnyRole)):
        return 'the requesting user lacks the required role'
    if isinstance(error, commands.NotOwner):
        return 'only the bot owner can use this command'
    if isinstance(error, commands.MissingRequiredArgument):
        return f'missing argument "{error.param.name}". Usage: {usage}'
    if isinstance(error, (commands.BadArgument, commands.BadUnionArgument)):
        return f'invalid argument ({error}). Usage: {usage}'
    if isinstance(error, commands.CommandOnCooldown):
        return f'command on cooldown, retry in {error.retry_after:.0f}s'
    if isinstance(error, commands.CheckFailure):
        return 'the requesting user is not allowed to use this command here'
    if isinstance(error, commands.CommandInvokeError):
        return f'the command crashed: {type(error.original).__name__}: {error.original}'
    return f'{type(error).__name__}: {error}'


class Bridge(commands.Cog, name="Bridge"):
    def __init__(self, bot):
        self.bot = bot
        self.runner = None
        self.captures = dict()  # {channel_id: [summaries of messages this bot sent]}

    # ---- lifecycle -----------------------------------------------------------

    async def cog_load(self):
        config = load_full_config()
        port = config.get(self.bot.bot_name, {}).get('bridge_port')
        if not port:
            self.bot.log.warning('Bridge: no bridge_port configured, bridge disabled')
            return
        bridge_conf = config.get('bridge', {}) or {}
        self.blocked_cogs = set(bridge_conf.get('blocked_cogs', DEFAULT_BLOCKED_COGS))
        self.blocked_commands = set(bridge_conf.get('blocked_commands', []))
        self.secret = get_bridge_secret()

        app = web.Application(client_max_size=64 * 1024)
        app.add_routes([
            web.get('/ping', self.handle_ping),
            web.get('/commands', self.handle_commands),
            web.post('/run', self.handle_run),
        ])
        self.runner = web.AppRunner(app, access_log=None)
        await self.runner.setup()
        try:
            await web.TCPSite(self.runner, BRIDGE_HOST, int(port), reuse_address=True).start()
            self.bot.log.info(f'Bridge listening on {BRIDGE_HOST}:{port}')
        except OSError as e:
            self.bot.log.error(f'Bridge could not listen on port {port}: {e}')
            await self.runner.cleanup()
            self.runner = None

    async def cog_unload(self):
        if self.runner is not None:
            await self.runner.cleanup()
            self.runner = None

    # ---- helpers -------------------------------------------------------------

    def authorized(self, request) -> bool:
        return hmac.compare_digest(request.headers.get('X-Bridge-Secret', ''), self.secret)

    def is_blocked(self, command: commands.Command) -> bool:
        root = command.root_parent or command
        return (command.hidden
                or root.qualified_name in self.blocked_commands
                or command.qualified_name in self.blocked_commands
                or (command.cog_name in self.blocked_cogs))

    def usage(self, command: commands.Command, prefix: str) -> str:
        return f'{prefix}{command.qualified_name} {command.signature}'.strip()

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.captures and message.author.id == self.bot.user.id and message.channel.id in self.captures:
            self.captures[message.channel.id].append(summarize_message(message))

    # ---- routes --------------------------------------------------------------

    async def handle_ping(self, request):
        if not self.authorized(request):
            return web.json_response({'error': 'unauthorized'}, status=401)
        return web.json_response({'name': self.bot.name, 'ready': self.bot.is_ready()})

    async def handle_commands(self, request):
        if not self.authorized(request):
            return web.json_response({'error': 'unauthorized'}, status=401)
        guild_id = request.query.get('guild_id')
        prefix = self.bot.prefix.get(int(guild_id), self.bot.default_prefix) if guild_id else self.bot.default_prefix
        result = list()
        for command in sorted(self.bot.walk_commands(), key=lambda c: c.qualified_name):
            if self.is_blocked(command):
                continue
            result.append({
                'usage': self.usage(command, prefix),
                'aliases': list(command.aliases),
                'description': command.description or command.short_doc or '',
                'category': command.cog_name or '',
            })
        return web.json_response({'name': self.bot.name, 'prefix': prefix, 'commands': result})

    async def handle_run(self, request):
        if not self.authorized(request):
            return web.json_response({'error': 'unauthorized'}, status=401)
        try:
            body = await request.json()
            guild_id = int(body['guild_id'])
            channel_id = int(body['channel_id'])
            message_id = int(body['message_id'])
            requester_id = int(body['requester_id'])
            command_line = str(body['command']).strip()
        except (KeyError, ValueError, TypeError):
            return web.json_response({'ok': False, 'error': 'bad request'}, status=400)

        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return web.json_response({'ok': False, 'error': f'{self.bot.name} is not in this server'})
        channel = guild.get_channel_or_thread(channel_id)
        if channel is None:
            return web.json_response({'ok': False, 'error': f'{self.bot.name} cannot see this channel'})
        try:
            member = guild.get_member(requester_id) or await guild.fetch_member(requester_id)
            base_message = await channel.fetch_message(message_id)
        except discord.HTTPException as e:
            return web.json_response({'ok': False, 'error': f'{self.bot.name} could not access the request: {e}'})

        prefix = self.bot.prefix.get(guild.id, self.bot.default_prefix)
        if command_line.startswith(prefix):
            command_line = command_line[len(prefix):]
        # Build a message that looks like the user typed the command (replying to GO-4's handoff message)
        message = copy.copy(base_message)
        message.author = member
        message.content = prefix + command_line
        context = await self.bot.get_context(message)

        if context.command is None:
            return web.json_response({'ok': False, 'error': f'unknown command "{command_line.split()[0] if command_line else ""}" for {self.bot.name}'})
        if self.is_blocked(context.command):
            return web.json_response({'ok': False, 'error': f'"{context.command.qualified_name}" cannot be run through GO-4'})

        usage = self.usage(context.command, prefix)
        self.bot.log.info(f'Bridge: running "{command_line}" for @{member.name} in #{channel.name}', guild)
        owns_capture = channel.id not in self.captures
        if owns_capture:
            self.captures[channel.id] = list()
        error = None
        try:
            self.bot.dispatch('command', context)
            if not await self.bot.can_run(context, call_once=True):
                raise commands.CheckFailure('global check failed')
            await asyncio.wait_for(context.command.invoke(context), timeout=COMMAND_TIMEOUT)
            self.bot.dispatch('command_completion', context)
        except commands.CommandError as e:
            error = describe_error(e, usage)
            await context.command.dispatch_error(context, e)  # the bot shows its usual error message
        except asyncio.TimeoutError:
            error = f'the command did not finish within {COMMAND_TIMEOUT}s'
        except Exception as e:
            error = f'{type(e).__name__}: {e}'
            self.bot.log.error(f'Bridge: unexpected error running "{command_line}": {error}', guild)
        await asyncio.sleep(OUTPUT_GRACE)
        output = self.captures.get(channel.id, []) if owns_capture else list()
        if owns_capture:
            self.captures.pop(channel.id, None)
        return web.json_response({
            'ok': error is None,
            'error': error,
            'command': context.command.qualified_name,
            'usage': usage,
            'bot_output': output[-5:],
        })


async def setup(bot):
    await bot.add_cog(Bridge(bot))
