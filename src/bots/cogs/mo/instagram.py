#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Command related to instagram and its API'''

#-------------------------------------------------------------------------------

import os
import re
import shutil
import asyncio
import functools
import discord
from discord.ext import commands
from discord.ext.commands import Context
import instaloader
from .utils import media_utils

tmp_download_dir = "tmp"
default_filesize_limit = 10 * 1024 * 1024  # Discord's upload limit for servers without boosts (and DMs) - 10MB
instagram_regex = r"https?://(?:www\.)?instagram\.com/\S*"

class Instagram(commands.Cog, name="Instagram"):
    def __init__(self, bot):
        self.bot = bot
        self.loader = None  # created on first use by get_loader
        self.loaded_session = None  # (path, modified time) of the session file the loader was created from, None if there was none

    @commands.command( name="show_insta", description="Download a post from instagram.")
    async def show_insta(self, context: Context, message: str):
        '''Download a media from instagram and show it'''
        match = re.match(instagram_regex, message)
        if match is not None:
            await self.send_media(message, context.reply, context.guild)
        else:
            embed = discord.Embed(
                    title="Sorry! There is some problem. :sweat:",
                    description="The message doesn't contain a valid instagram link.",
                    color=self.bot.default_color,
                    )
            await context.reply(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        ''' Watch for instagram links in any channel and send the media'''
        if message.guild is None or message.author.bot or message.content == "":
            return
        match = re.search(instagram_regex, message.content)
        if match is not None and len(message.content.split("/")) >= 5:
            # Link is of a media - get the media and send it
            self.bot.log.info("Got a link of a media from "+message.guild.name, message.guild)
            await self.send_media(match.group(0), message.reply, message.guild)

    async def send_media(self, instagram_url, replier, guild=None):
        ''' Download the media from instagram and send it'''
        max_num_attachment = 10  # Maximum files per message
        max_attachment_size = guild.filesize_limit if guild is not None else default_filesize_limit  # Maximum upload size per message - depends on the server boost level
        max_size_text = f"{round(max_attachment_size / (1024 * 1024))}MB"
        url_parts = instagram_url.split("?")[0].split("/")
        media_type = url_parts[3] if len(url_parts) > 4 else ""
        if media_type not in ("p", "reel"):
            embed = discord.Embed(
                    title="Sorry! There is some problem. :sweat:",
                    description="The link doesn't contain a valid instagram media type. Supported types are post and reel.",
                    color=self.bot.default_color,
                    )
            await replier(embed=embed)
            self.bot.log.warning("Failed to get media. Invalid instagram media type from "+str(instagram_url), guild)
            return
        shortcode = url_parts[4]  # also used as the download folder name
        request_dir = os.path.join(tmp_download_dir, shortcode)
        os.makedirs(request_dir, exist_ok=True)
        allowed_file_types = [".jpg", ".png", ".jpeg", ".gif", ".mp4"] if media_type == "p" else [".mp4"]
        post = await self.download_post(shortcode, guild)
        if post is None:
            embed = discord.Embed(
                    title="Sorry! There is some problem. :sweat:",
                    description="A exception occured while trying to download the media. Possibly the user is private, the media doesn't exist or instagram is limiting requests.",
                    color=self.bot.default_color,
                    )
            await replier(embed=embed)
            self.bot.log.warning("Failed to get media. Exception occured while trying to download the media from "+str(instagram_url), guild)
            shutil.rmtree(request_dir, ignore_errors=True)
            return
        media_files = list()
        for file in os.listdir(request_dir):
            if any(file.endswith(ext) for ext in allowed_file_types):
                file_path = os.path.join(request_dir, file)
                media_files.append({"path": file_path, "size": os.path.getsize(file_path)})
        self.bot.log.info("Downloaded "+str(len(media_files))+" files from instagram", guild)
        media_files = await self.fit_media_files(media_files, max_attachment_size, guild)
        embed = self.get_media_description(post, guild)
        # Check if any file still exceeds the maximum size after compression/splitting
        skip_files = [file for file in media_files if file["size"] > max_attachment_size]
        media_files = [file for file in media_files if file["size"] <= max_attachment_size]
        skipped_sizes = [f"{round(file['size'] / (1024 * 1024), 2)}MB" for file in skip_files]
        if len(skip_files) > 0:
            embed.description = embed.description + f"\nSkipped {len(skip_files)} files ({', '.join(skipped_sizes)}) because they exceed the maximum attachment size of {max_size_text}"
            self.bot.log.info(f"Skipped {len(skip_files)} files ({', '.join(skipped_sizes)}) because they exceed the maximum attachment size of {max_size_text}", guild)
        if len(media_files) == 0:
            embed.description = f"Sorry! There is some problem. :sweat:\nAll files exceed the maximum attachment size of {max_size_text}:  ({', '.join(skipped_sizes)})"
            await replier(embed=embed)
            self.bot.log.warning(f"Failed to send media. All files exceed the maximum attachment size of {max_size_text} ({', '.join(skipped_sizes)})", guild)
            shutil.rmtree(request_dir, ignore_errors=True)
            return
        #Send files in batches that fit in one message (file count and total size)
        batches = media_utils.group_media_files(media_files, max_num_attachment, max_attachment_size)
        num_files = len(media_files)
        original_description = embed.description
        num_sent = 0
        for batch in batches:
            if len(batches) > 1:
                embed.description = original_description + f"\nShowing {num_sent+1} to {num_sent+len(batch)} of {num_files} files"
            await replier(embed=embed, files=[file["file"] for file in batch])
            self.bot.log.info(f"Sending {num_sent+1} to {num_sent+len(batch)} of {num_files} attachments from instagram", guild)
            num_sent += len(batch)
        shutil.rmtree(request_dir, ignore_errors=True)

    async def fit_media_files(self, media_files, max_size, guild=None):
        ''' compress or split any file exceeding max_size (runs in executor to avoid blocking event loop)'''
        loop = asyncio.get_event_loop()
        fitted_files = list()
        for file in media_files:
            if file["size"] <= max_size:
                fitted_files.append({"file": discord.File(file["path"]), "size": file["size"], "path": file["path"]})
                continue
            self.bot.log.info("Compressing/splitting oversized file "+file["path"], guild)
            try:
                part_paths = await loop.run_in_executor(None, functools.partial(
                    media_utils.get_media_parts, file["path"], max_size))
            except Exception as e:
                self.bot.log.warning("Failed to compress/split "+file["path"]+": "+str(e), guild)
                fitted_files.append({"file": discord.File(file["path"]), "size": file["size"], "path": file["path"]})
                continue
            for part_path in part_paths:
                fitted_files.append({"file": discord.File(part_path), "size": os.path.getsize(part_path), "path": part_path})
        return fitted_files

    async def download_post(self, shortcode, guild=None):
        ''' download a post or reel from instagram shortcode (runs in executor to avoid blocking event loop)'''
        loader = self.get_loader(guild)
        mode = "logged in as "+str(loader.context.username) if loader.context.is_logged_in else "anonymous"
        try:
            loop = asyncio.get_event_loop()
            post = await loop.run_in_executor(None, functools.partial(
                instaloader.Post.from_shortcode, loader.context, shortcode))
            await loop.run_in_executor(None, functools.partial(
                loader.download_post, post, target=shortcode))
            return post
        except (instaloader.exceptions.InstaloaderException, instaloader.exceptions.AbortDownloadException) as e:
            # AbortDownloadException (e.g. feedback_required) is not a subclass of InstaloaderException
            self.bot.log.warning(f"Instagram request failed ({mode}): {e}", guild)
            return None

    def get_media_description(self, post, guild=None):
        ''' Get a description of the media to send in embed (only uses data already fetched with the post)'''
        embed = discord.Embed(title="Instagram Media", color=self.bot.default_color)
        try:
            caption = (post.caption or "No caption").split("\n")[0]
            short_caption = caption if len(caption) < 50 else caption[:50] + "..."
            embed.title = "@"+str(post.owner_username)
            embed.url = f"https://www.instagram.com/{post.owner_username}"
            embed.description = f"Caption: {short_caption}\nLikes: {post.likes}"
        except Exception as e:
            self.bot.log.warning(f"get_media_description failed: {e}", guild)
        return embed

    def new_loader(self):
        ''' Create an anonymous instaloader that downloads into the tmp directory'''
        return instaloader.Instaloader(sleep=True, quiet=True,
                                       download_pictures = True, download_videos= True,
                                       download_video_thumbnails = False, save_metadata= False,
                                       dirname_pattern=os.path.join(tmp_download_dir, '{target}'))

    def get_loader(self, guild : discord.Guild = None):
        ''' Get the loader - logged in if a session file is present, anonymous otherwise'''
        # the session file is checked on every request, so copying in or deleting a session file takes effect without a reload
        session_file = self.get_session_file()
        session = (session_file, os.path.getmtime(session_file)) if session_file is not None else None
        if self.loader is not None and session == self.loaded_session:
            return self.loader
        self.loader = self.new_loader()
        self.loaded_session = session  # remembered even if loading fails, so a broken file is not retried on every request
        if session_file is None:
            self.bot.log.info("No instagram session found, using anonymous access", guild)
            return self.loader
        username = os.path.basename(session_file).split("-", 1)[1]
        try:
            self.loader.load_session_from_file(username, session_file)
            self.bot.log.info("Loaded session of "+str(username), guild)
        except Exception as e:
            self.loader = self.new_loader()
            self.bot.log.warning("Failed to load session of "+str(username)+", using anonymous access: "+str(e), guild)
        return self.loader

    @commands.command(name="login_instagram", description="Log in to instagram.")
    @commands.has_permissions(administrator=True)
    async def login_instagram(self, context: Context):
        '''Get instagram credentials privately in dm and log in to instagram'''
        embed = discord.Embed(
            title="Instagram credentials",
            description="Please open your DMs to provide your instagram credentials.",
            color=self.bot.default_color,
            )
        await context.reply(embed=embed)
        _username, _password = await self._get_instagram_credentials(context)
        if _username is None or _password is None:
            return
        embed = discord.Embed(
            title="Instagram credentials",
            description="Credentials received. Trying to log in to instagram.",
            color=self.bot.default_color,
            )
        await context.author.send(embed=embed)
        await context.reply(embed=embed)
        if await self._login_instagram(context, _username, _password):
            embed = discord.Embed(
                title="Instagram credentials",
                description="Logged in to instagram as "+str(_username),
                color=self.bot.default_color,
                )
            await context.reply(embed=embed)
        else:
            embed = discord.Embed(
                title="Instagram credentials",
                description="Failed to log in to instagram as "+str(_username)+". Please try again.",
                color=self.bot.default_color,
                )
            await context.reply(embed=embed)

    @commands.command(name="logout_instagram", description="Log out of instagram and remove the session.", aliases=["clear_instagram_session"])
    @commands.has_permissions(administrator=True)
    async def logout_instagram(self, context: Context):
        '''Log out of instagram by removing the session'''
        self.clear_session(context.guild)
        self.bot.log.info("Logged out of instagram.", context.guild)
        embed = discord.Embed(
            title="Instagram session",
            description="Logged out of instagram. Media will be downloaded anonymously.",
            color=self.bot.default_color,
            )
        await context.reply(embed=embed)

    async def _get_instagram_credentials(self, context: Context):
        '''Get instagram credentials in dm'''
        check = lambda message: message.author == context.author and message.channel == context.author.dm_channel
        try:
            embed = discord.Embed(
                title="Instagram credentials",
                description="Please provide your instagram username.",
                color=self.bot.default_color,
                )
            await context.author.send(embed=embed)
            message = await self.bot.wait_for('message', timeout=60.0, check=check)
            _username = message.content
            embed = discord.Embed(
                title="Instagram credentials",
                description="Please provide your instagram password.",
                color=self.bot.default_color,
                )
            await context.author.send(embed=embed)
            message = await self.bot.wait_for('message', timeout=60.0, check=check)
            _password = message.content
            return _username, _password
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="Instagram credentials",
                description="You took too long to provide your instagram credentials. Please try again.",
                color=self.bot.default_color,
                )
            await context.author.send(embed=embed)
            await context.reply(embed=embed)
            self.bot.log.warning("User took too long to provide instagram credentials.", context.guild)
            return None, None
        except discord.Forbidden:
            embed = discord.Embed(
                title="Instagram credentials",
                description="I couldn't send you a DM. Please enable DMs from server members.",
                color=self.bot.default_color,
                )
            await context.reply(embed=embed)
            self.bot.log.warning("Couldn't send DM to user "+str(context.author.name), context.guild)
            return None, None

    async def _login_instagram(self, context: Context, username: str, password: str):
        '''Log in to instagram and save the session (overrides the existing session)'''
        # no test_login() check after logging in - it is a graphql query that fails on a rate limited account even when the login worked
        loader = self.new_loader()
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, functools.partial(loader.login, username, password))
            self.bot.log.info("Logged in to instagram as "+str(username), context.guild)
        except instaloader.exceptions.InstaloaderException as e:
            self.bot.log.warning("Failed to log in to instagram as "+str(username)+". Exception raised by instaloader: "+str(e), context.guild)
            return False
        self.save_session(loader, username, context.guild)
        return True

    def get_session_file(self):
        ''' Get the path of the shared session file (one instagram login is shared across all guilds), None if there is none'''
        session_dir = self.bot.bot_data_path("session")
        if not os.path.exists(session_dir):
            return None
        session_files = sorted(file for file in os.listdir(session_dir) if file.startswith("session-"))
        if len(session_files) == 0:
            return None
        return os.path.join(session_dir, session_files[0])

    def save_session(self, loader, username, guild : discord.Guild):
        # save the shared session to file (one instagram login is shared across all guilds) - picked up by get_loader on the next request
        session_dir = self.bot.bot_data_path("session")
        self.clear_session(guild)
        session_file = os.path.join(session_dir, f"session-{username}")
        loader.save_session_to_file(session_file)
        self.bot.log.info("Saved session of "+str(username), guild)

    def clear_session(self, guild : discord.Guild):
        # clear the shared session (one instagram login is shared across all guilds) - next request is anonymous
        session_dir = self.bot.bot_data_path("session")
        if os.path.exists(session_dir):
            shutil.rmtree(session_dir)
            self.bot.log.info("Cleared session", guild)
        else:
            self.bot.log.info("No existing session found", guild)
        self.loader = None
        self.loaded_session = None


async def setup(bot):
    await bot.add_cog(Instagram(bot))
