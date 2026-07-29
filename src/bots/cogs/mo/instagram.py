#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Command related to instagram and its API'''

#-------------------------------------------------------------------------------

import os
import re
import math
import shutil
import asyncio
import functools
import discord
from discord.ext import commands
from discord.ext.commands import Context
import instaloader

tmp_download_dir = "tmp"
instagram_regex = r"https?://(?:www\.)?instagram\.com/\S*"

class Instagram(commands.Cog, name="Instagram"):
    def __init__(self, bot):
        self.bot = bot
        self.loader = instaloader.Instaloader(sleep=True, quiet=True,
                                              download_pictures = True, download_videos= True,
                                              download_video_thumbnails = False, save_metadata= False)

    @commands.command( name="show", description="Download a post from instagram.")
    async def show(self, context: Context, message: str):
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
        max_attachment_size = 25 * 1024 * 1024  # Maximum size of individual attachment - 25MB
        if not self.loader.context.is_logged_in:
            self.load_session(guild) # load the session if available
        if not self.loader.context.is_logged_in:
            self.bot.log.warning("Not logged in to instagram, skipping media fetch for "+str(instagram_url), guild)
            return
        media_type = instagram_url.split("/")[3]
        if media_type == "p":
            media = await self.download_media_from_shortcode(instagram_url.split("/")[-2])
            allowed_file_types = [".jpg", ".png", ".jpeg", ".gif", ".mp4"]
        elif media_type == "reel":
            media = await self.download_media_from_shortcode(instagram_url.split("/")[-2])
            allowed_file_types = [".mp4"]
        elif media_type == "stories":
            media = await self.download_stories_from_username(instagram_url.split("/")[-2])
            allowed_file_types = [".jpg", ".png", ".jpeg", ".gif", ".mp4"]
        else:
            embed = discord.Embed(
                    title="Sorry! There is some problem. :sweat:",
                    description="The link doesn't contain a valid instagram media type. Supported types are post, reel and stories.",
                    color=self.bot.default_color,
                    )
            await replier(embed=embed)
            self.bot.log.warning("Failed to get media. Invalid instagram media type from "+str(instagram_url), guild)
            return
        if media is None:
            embed = discord.Embed(
                    title="Sorry! There is some problem. :sweat:",
                    description="A exception occured while trying to download the media. Possibly the user is private or the media doesn't exist.",
                    color=self.bot.default_color,
                    )
            await replier(embed=embed)
            self.bot.log.warning("Failed to get media. Exception occured while trying to download the media from "+str(instagram_url), guild)
            return
        media_files = list()
        for file in os.listdir(os.getcwd()+"/"+tmp_download_dir):
            if any(file.endswith(ext) for ext in allowed_file_types):
                media_file = discord.File(tmp_download_dir+"/"+file)
                size = os.path.getsize(tmp_download_dir+"/"+file) # in bytes
                media_files.append({"file": media_file, "size": size})
        self.bot.log.info("Downloaded "+str(len(media_files))+" files from instagram", guild)
        for item in os.listdir(tmp_download_dir):
            item_path = os.path.join(tmp_download_dir, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
        embed = self.get_media_description(media, media_type, guild)
        # Check if any file exceeds the maximum size
        skip_files = list()
        for file in media_files:
            if file["size"] > max_attachment_size:
                skip_files.append(file)
                media_files.remove(file)
        skipped_sizes = [f"{round(file['size'] / (1024 * 1024), 2)}MB" for file in skip_files]
        if len(skip_files) > 0:
            embed.description = embed.description + f"\nSkipped {len(skip_files)} files ({', '.join(skipped_sizes)}) because they exceed the maximum attachment size of 25MB"
            self.bot.log.info(f"Skipped {len(skip_files)} files ({', '.join(skipped_sizes)}) because they exceed the maximum attachment size of 25MB", guild)
        if len(media_files) == 0:
            embed.description = f"Sorry! There is some problem. :sweat:\nAll files exceed the maximum attachment size of 25MB:  ({', '.join(skipped_sizes)})"
            await replier(embed=embed)
            self.bot.log.warning(f"Failed to send media. All files exceed the maximum attachment size of 25MB ({', '.join(skipped_sizes)})", guild)
            return
        num_files = len(media_files)
        if num_files > max_num_attachment:
            #Send files in chunks (split files evenly)
            chunk_size = min(max_num_attachment, math.ceil(num_files / math.ceil(num_files / max_num_attachment)))
            original_description = embed.description
            for i in range(0, num_files, chunk_size):
                embed.description = original_description + f"\nShowing {i+1} to {min(i + chunk_size, num_files)} of {num_files} files"
                await replier(embed=embed, files=[file["file"] for file in media_files[i:i + chunk_size]])
                self.bot.log.info(f"Sending {i+1} to {min(i + chunk_size, num_files)} of {num_files} attachments from instagram", guild)
        else:
            #Send all files in one message
            await replier(embed=embed, files=[file["file"] for file in media_files])
            self.bot.log.info(f"Sending {num_files} attachments from instagram", guild)

    async def download_media_from_shortcode(self, shortcode):
        ''' download a media from instagram shortcode (runs in executor to avoid blocking event loop)'''
        try:
            loop = asyncio.get_event_loop()
            post = await loop.run_in_executor(None, functools.partial(
                instaloader.Post.from_shortcode, self.loader.context, shortcode))
            await loop.run_in_executor(None, functools.partial(
                self.loader.download_post, post, target=tmp_download_dir))
            return post
        except instaloader.exceptions.InstaloaderException as e:
            return None

    async def download_stories_from_username(self, username):
        ''' download a story from instagram username (runs in executor to avoid blocking event loop)'''
        try:
            loop = asyncio.get_event_loop()
            profile = await loop.run_in_executor(None, functools.partial(
                instaloader.Profile.from_username, self.loader.context, username))
            await loop.run_in_executor(None, functools.partial(
                self.loader.download_stories, [profile.userid], filename_target=tmp_download_dir))
            return profile
        except instaloader.exceptions.InstaloaderException as e:
            return None

    def get_media_description(self, media, media_type, guild=None):
        ''' Get a description of the media to send in embed'''
        embed = discord.Embed(title="Instagram Media", color=self.bot.default_color)
        try:
            if media_type in ("p", "reel"):
                owner = getattr(media, "owner_profile", None)
                caption = (getattr(media, "caption", "") or "No caption").split("\n")[0]
                short_caption = caption if len(caption) < 50 else caption[:50] + "..."
                embed.title = getattr(owner, "full_name", "Unknown")
                embed.url = f"https://www.instagram.com/{getattr(owner, 'username', 'unknown')}"
                embed.description = f"Caption: {short_caption}\nLikes: {getattr(media, 'likes', 'Unknown')}"
                if owner and getattr(owner, "profile_pic_url", None):
                    embed.set_thumbnail(url=owner.profile_pic_url)
            elif media_type == "stories":
                embed.title = getattr(media, "full_name", "Unknown")
                embed.url = f"https://www.instagram.com/{getattr(media, 'username', 'unknown')}"
                if getattr(media, "profile_pic_url", None):
                    embed.set_thumbnail(url=media.profile_pic_url)
        except Exception as e:
            self.bot.log.warning(f"get_media_description failed: {e}", guild)
        return embed

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
            self.save_session(context.guild)
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

    @commands.command(name="clear_instagram_session", description="Remove the instagram session.")
    @commands.has_permissions(administrator=True)
    async def clear_instagram_session(self, context: Context):
        '''Clear the instagram session'''
        self.clear_session(context.guild)
        self.bot.log.info("Cleared instagram session.", context.guild)  
        embed = discord.Embed(
            title="Instagram session",
            description="Cleared instagram session.",
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
        '''Log in to instagram'''
        try:
            self.loader.context.login(username, password)
            self.bot.log.info("Logged in to instagram as "+str(username), context.guild)
            if self.loader.context.test_login() != username:
                self.bot.log.warning("Test login failed. Couldn't log in to instagram as "+str(username), context.guild)
                return False
            return True
        except instaloader.exceptions.InstaloaderException as e:
            self.bot.log.warning("Failed to log in to instagram as "+str(username)+". Exception raised by instaloader: "+str(e), context.guild)
            return False
    
    def load_session(self, guild : discord.Guild):
        # load the shared session from file (one instagram login is shared across all guilds)
        session_dir = self.bot.bot_data_path("session")
        if os.path.exists(session_dir) and len(os.listdir(session_dir)) > 0:
            session_file = os.path.join(session_dir, os.listdir(session_dir)[0])
            username = os.listdir(session_dir)[0].split("-")[1]
            self.loader.load_session_from_file(username, session_file)
            self.bot.log.info("Loaded session of "+str(username), guild)
        else:
            self.bot.log.warning("No session found", guild)

    def save_session(self, guild : discord.Guild):
        # save the shared session to file (one instagram login is shared across all guilds)
        session_dir = self.bot.bot_data_path("session")
        self.clear_session(guild)
        username = self.loader.test_login()
        session_file = os.path.join(session_dir, f"session-{username}")
        self.loader.save_session_to_file(session_file)
        self.bot.log.info("Saved session of "+str(username), guild)

    def clear_session(self, guild : discord.Guild):
        # clear the shared session (one instagram login is shared across all guilds)
        session_dir = self.bot.bot_data_path("session")
        if os.path.exists(session_dir):
            shutil.rmtree(session_dir)
            self.bot.log.info("Cleared session", guild)
        else:
            self.bot.log.info("No existing session found", guild)


async def setup(bot):
    await bot.add_cog(Instagram(bot))