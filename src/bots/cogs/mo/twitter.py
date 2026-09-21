#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Command related to twitter/x and its API'''

#-------------------------------------------------------------------------------

import os
import re
import math
import asyncio
import functools
import requests
import discord
from discord.ext import commands
from discord.ext.commands import Context
from .utils import twitter_client
from .utils import media_utils

tmp_download_dir = "tmp"
twitter_regex = r"https?://(?:www\.)?(?:twitter|x)\.com/\S*"

class Twitter(commands.Cog, name="Twitter"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command( name="show_tweet", description="Download a post from twitter.")
    async def show_tweet(self, context: Context, message: str):
        '''Download a media from twitter and show it'''
        match = re.match(twitter_regex, message)
        if match is not None:
            await self.send_media(message, context.reply, context.guild)
        else:
            embed = discord.Embed(
                    title="Sorry! There is some problem. :sweat:",
                    description="The message doesn't contain a valid twitter link.",
                    color=self.bot.default_color,
                    )
            await context.reply(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        ''' Watch for twitter links in any channel and send the media'''
        if message.guild is None or message.author.bot or message.content == "":
            return
        match = re.search(twitter_regex, message.content)
        if match is not None and "/status/" in message.content:
            # Link is of a tweet - get the media and send it
            self.bot.log.info("Got a link of a media from "+message.guild.name, message.guild)
            await self.send_media(match.group(0), message.reply, message.guild)

    async def send_media(self, twitter_url, replier, guild=None):
        ''' Download the media from twitter and send it'''
        max_num_attachment = 10  # Maximum files per message
        max_attachment_size = 25 * 1024 * 1024  # Maximum size of individual attachment - 25MB
        tweet_id = twitter_client.extract_tweet_id(twitter_url)
        if tweet_id is None:
            embed = discord.Embed(
                    title="Sorry! There is some problem. :sweat:",
                    description="The link doesn't contain a valid twitter status.",
                    color=self.bot.default_color,
                    )
            await replier(embed=embed)
            self.bot.log.warning("Failed to get media. Invalid twitter link from "+str(twitter_url), guild)
            return
        status = await self.fetch_tweet_status(tweet_id)
        if status is None:
            embed = discord.Embed(
                    title="Sorry! There is some problem. :sweat:",
                    description="A exception occured while trying to fetch the tweet. Possibly the tweet is private or doesn't exist.",
                    color=self.bot.default_color,
                    )
            await replier(embed=embed)
            self.bot.log.warning("Failed to fetch tweet. Exception occured while trying to fetch the tweet from "+str(twitter_url), guild)
            return
        media_list = status.get('extended_entities', {}).get('media', [])
        if len(media_list) == 0:
            embed = discord.Embed(
                    title="Sorry! There is some problem. :sweat:",
                    description="The tweet doesn't contain any media.",
                    color=self.bot.default_color,
                    )
            await replier(embed=embed)
            self.bot.log.warning("Failed to get media. No media found in tweet from "+str(twitter_url), guild)
            return
        media_files = await self.download_media(tweet_id, media_list)
        self.bot.log.info("Downloaded "+str(len(media_files))+" files from twitter", guild)
        media_files = await self.fit_media_files(media_files, max_attachment_size, guild)
        embed = self.get_media_description(status)
        # Check if any file still exceeds the maximum size after compression/splitting
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
            self.cleanup_files(media_files + skip_files)
            return
        num_files = len(media_files)
        if num_files > max_num_attachment:
            #Send files in chunks (split files evenly)
            chunk_size = min(max_num_attachment, math.ceil(num_files / math.ceil(num_files / max_num_attachment)))
            original_description = embed.description
            for i in range(0, num_files, chunk_size):
                embed.description = original_description + f"\nShowing {i+1} to {min(i + chunk_size, num_files)} of {num_files} files"
                await replier(embed=embed, files=[file["file"] for file in media_files[i:i + chunk_size]])
                self.bot.log.info(f"Sending {i+1} to {min(i + chunk_size, num_files)} of {num_files} attachments from twitter", guild)
        else:
            #Send all files in one message
            await replier(embed=embed, files=[file["file"] for file in media_files])
            self.bot.log.info(f"Sending {num_files} attachments from twitter", guild)
        self.cleanup_files(media_files + skip_files)

    async def fit_media_files(self, media_files, max_size, guild=None):
        ''' compress or split any file exceeding max_size (runs in executor to avoid blocking event loop)'''
        loop = asyncio.get_event_loop()
        fitted_files = list()
        for file in media_files:
            if file["size"] <= max_size:
                fitted_files.append(file)
                continue
            self.bot.log.info("Compressing/splitting oversized file "+file["path"], guild)
            try:
                part_paths = await loop.run_in_executor(None, functools.partial(
                    media_utils.get_media_parts, file["path"], max_size))
            except Exception as e:
                self.bot.log.warning("Failed to compress/split "+file["path"]+": "+str(e), guild)
                fitted_files.append(file)
                continue
            for part_path in part_paths:
                fitted_files.append({"file": discord.File(part_path), "size": os.path.getsize(part_path), "path": part_path})
        return fitted_files

    async def fetch_tweet_status(self, tweet_id):
        ''' fetch a tweet's status from twitter (runs in executor to avoid blocking event loop)'''
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, functools.partial(
            twitter_client.get_tweet_status, tweet_id))

    async def download_media(self, tweet_id, media_list):
        ''' download the media of a tweet (runs in executor to avoid blocking event loop)'''
        loop = asyncio.get_event_loop()
        os.makedirs(tmp_download_dir, exist_ok=True)
        media_files = list()
        session = requests.Session()
        for index, media in enumerate(media_list, start=1):
            extension = "jpg" if media.get('type') == "photo" else "mp4"
            file_path = os.path.join(tmp_download_dir, f"{tweet_id}_{index}.{extension}")
            success = await loop.run_in_executor(None, functools.partial(
                twitter_client.download_media_item, session, file_path, media))
            if not success:
                continue
            media_files.append({"file": discord.File(file_path), "size": os.path.getsize(file_path), "path": file_path})
        return media_files

    def cleanup_files(self, media_files):
        ''' remove downloaded media files from the tmp directory'''
        for file in media_files:
            if os.path.exists(file["path"]):
                os.remove(file["path"])

    def get_media_description(self, status):
        ''' Get a description of the tweet to send in embed'''
        user = status.get('user', {})
        embed = discord.Embed(title="Twitter Media", color=self.bot.default_color)
        try:
            caption = (status.get('full_text', '') or "No caption").split("\n")[0]
            short_caption = caption if len(caption) < 50 else caption[:50] + "..."
            embed.title = user.get("name", "Unknown")
            embed.url = f"https://twitter.com/{user.get('screen_name', 'unknown')}"
            embed.description = f"Caption: {short_caption}\nLikes: {status.get('favorite_count', 'Unknown')}\nReposts: {status.get('retweet_count', 'Unknown')}"
            if user.get("profile_image_url_https"):
                embed.set_thumbnail(url=user.get("profile_image_url_https"))
        except Exception as e:
            self.bot.log.warning(f"get_media_description failed: {e}")
        return embed

async def setup(bot):
    await bot.add_cog(Twitter(bot))
