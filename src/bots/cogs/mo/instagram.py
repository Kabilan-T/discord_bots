#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Command related to instagram and its API'''

#-------------------------------------------------------------------------------

import os
import re
import yaml
import math
import asyncio
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
        # channels to watch for instagram links
        self.channels_to_watch = dict()
        self.load_channel_watch_list()

    @commands.command( name="bio", description="Get the bio of a user.")
    async def bio(self, context: Context, username: str):
        '''Get the bio of a user'''
        await self.send_bio(context.reply, username, context.guild)

    @commands.command( name="show", description="Download a post from instagram.")
    async def show(self, context: Context, message: str):
        '''Download a media from instagram and show it'''
        match = re.match(instagram_regex, message)
        if match is not None:
            print("Matched")
            await self.send_media(context.reply, message, context.guild)
        else:
            embed = discord.Embed(
                    title="Sorry! There is some problem. :sweat:",
                    description="The message doesn't contain a valid instagram link.",
                    color=self.bot.default_color,
                    )
            await context.reply(embed=embed)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        ''' Watch for instagram links and send the media'''
        if message.guild is None or message.author.bot or message.content == "":
            return
        if str(message.channel.id) in self.channels_to_watch.get(str(message.guild.id), []):
            match = re.search(instagram_regex, message.content)
            if match is not None:
                if len(message.content.split("/")) == 4:
                    # Link is of a profile - get the bio
                    self.bot.log.info("Got a link of a profile from "+message.channel.name, message.guild)
                    await self.send_bio(match.group(0), message.reply, message.guild)
                elif len(message.content.split("/")) >= 5:
                    # Link is of a media - get the media and send it
                    self.bot.log.info("Got a link of a media from "+message.guild.name, message.guild)
                    await self.send_media(match.group(0), message.reply, message.guild)
                else:
                    return
    
    async def send_bio(self, instagram_url, replier, guild=None):
        # send the bio of a user
        if instagram_url.startswith("@"):
            username = instagram_url[1:]
        else:
            username = instagram_url.split("/")[-1]
        try:    
            profile = instaloader.Profile.from_username(self.loader.context, username)
            embed = discord.Embed(
                    title=str(profile.full_name),
                    url="https://www.instagram.com/"+str(profile.username),
                    description=profile.biography,
                    color=self.bot.default_color,
                    )
            embed.set_thumbnail(url=profile.profile_pic_url)
            embed.add_field(name="Followers", value=str(profile.followers), inline=True)
            embed.add_field(name="Following", value=str(profile.followees), inline=True)
            embed.add_field(name="Posts", value=str(profile.mediacount), inline=True)
            await replier(embed=embed)
            self.bot.log.info("Sent bio of @"+str(profile.username), guild)
        except instaloader.exceptions.InstaloaderException:
            embed = discord.Embed(
                    title="Sorry! There is some problem. :sweat:",
                    description="Possibly the username is wrong or doesn't exist.",
                    color=self.bot.default_color,
                    )
            await replier(embed=embed)
            self.bot.log.warning("Failed to send bio of "+str(username), guild)
    
    async def send_media(self, instagram_url, replier, guild=None):
        # download a media from instagram url and send it
        max_num_attachment = 10  # Maximum files per message
        max_attachment_size = 25 * 1024 * 1024  # Maximum size of individual attachment - 25MB
        if not self.loader.context.is_logged_in:
            self.load_session(guild) # load the session if available
        media_type = instagram_url.split("/")[3]    
        if media_type == "p":
            media_files, embed = await self.get_post(instagram_url, guild)
        elif media_type == "reel":
            media_files, embed = await self.get_reel(instagram_url, guild)
        elif media_type == "stories":
            media_files, embed = await self.get_stories(instagram_url, guild)
        # Send the media
        if media_files is None:
            await replier(embed=embed)
            self.bot.log.warning("Failed to send media from "+str(instagram_url), guild)
            return
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

    async def get_post(self, instagram_url, guild=None):
        # get a post from the url
        shortcode = instagram_url.split("/")[-2] # (https://www.instagram.com/p/<shortcode>/<post_id>)
        try:
            #Find the post from the url
            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
            # Download the post
            self.loader.download_post(post, target=tmp_download_dir)
            media_files = list()
            for file in os.listdir(os.getcwd()+"/"+tmp_download_dir):
                if file.endswith(".jpg") or file.endswith(".mp4") or file.endswith(".png") or file.endswith(".jpeg") or file.endswith(".gif"):
                    media_file = discord.File(tmp_download_dir+"/"+file)
                    size = os.path.getsize(tmp_download_dir+"/"+file) # in bytes
                    media_files.append({"file": media_file, "size": size})
            self.bot.log.info("Downloaded "+str(len(media_files))+" files from @"+str(post.owner_profile.username)+"'s post", guild)
            os.system("rm -rf "+tmp_download_dir+"/*")
            # Create an embed message with the post
            if post.caption is not None:
                short_caption = post.caption.split("\n")[0] if len(post.caption.split("\n")[0]) < 50  else post.caption.split("\n")[0][:50]+"..."
            else:
                short_caption = "No caption"
            embed = discord.Embed(
                title=str(post.owner_profile.full_name),
                url="https://www.instagram.com/"+str(post.owner_profile.username),
                description="Caption: "+str(short_caption)+"\nType: Post\nLikes: "+str(post.likes)+"\n",
                color=self.bot.default_color,
                )
            embed.set_thumbnail(url=post.owner_profile.profile_pic_url)
            return media_files, embed
        except instaloader.exceptions.InstaloaderException as e:
            embed = discord.Embed(
                    title="Sorry! There is some problem.",
                    description="A exception occured while trying to download the post. Possibly the user is private or the post doesn't exist.",
                    color=self.bot.default_color,
                    )
            return None, embed

    async def get_reel(self, instagram_url, guild=None):
        # get a reel from the url
        shortcode = instagram_url.split("/")[-2] # (https://www.instagram.com/reel/<shortcode>/<post_id>)
        try:
            #Find the reel from the url
            reel = instaloader.Post.from_shortcode(self.loader.context, shortcode)
            # Download the reel
            self.loader.download_post(reel, target=tmp_download_dir)
            media_files = list()
            for file in os.listdir(os.getcwd()+"/"+tmp_download_dir):
                if file.endswith(".mp4"):
                    media_file = discord.File(tmp_download_dir+"/"+file)
                    size = os.path.getsize(tmp_download_dir+"/"+file)
                    media_files.append({"file": media_file, "size": size})
            self.bot.log.info("Downloaded "+str(len(media_files))+" files from @"+str(reel.owner_profile.username)+"'s reel", guild)
            os.system("rm -rf "+tmp_download_dir+"/*")
            # create an embed message with the reel
            if reel.caption is not None:
                short_caption = reel.caption.split("\n")[0] if len(reel.caption.split("\n")[0]) < 50  else reel.caption.split("\n")[0][:50]+"..."
            else:
                short_caption = "No caption"
            embed = discord.Embed(
                title=str(reel.owner_profile.full_name),
                url="https://www.instagram.com/"+str(reel.owner_profile.username),
                description="Caption: "+str(short_caption)+"\nType: Reel\nLikes: "+str(reel.likes)+"\n",
                color=self.bot.default_color,
                )
            embed.set_thumbnail(url=reel.owner_profile.profile_pic_url)
            return media_files, embed
        except instaloader.exceptions.InstaloaderException as e:
            embed = discord.Embed(
                    title="Sorry! There is some problem. :sweat:",
                    description="A exception occured while trying to download the reel. Possibly the user is private or the reel doesn't exist.",
                    color=self.bot.default_color,
                    )
            return None, embed

    async def get_stories(self, instagram_url, guild=None):
        # get a story from the url
        username = instagram_url.split("/")[4]
        # stories requires login
        if not self.loader.context.is_logged_in:
            embed = discord.Embed(
                title="Sorry! There is some problem. :sweat:",
                description="Stories can be downloaded only if the bot is logged in. There is no login credentials provided to log in to instagram.",
                color=self.bot.default_color,
                )
            self.bot.log.warning("Failed to get story. No login credentials provided.", guild)
            return None, embed
        # get the story
        try:
            profile = instaloader.Profile.from_username(self.loader.context, username)
            # Download the story
            self.loader.download_stories([profile.userid],  filename_target=tmp_download_dir)
            media_files = list()
            for file in os.listdir(os.getcwd()+"/"+tmp_download_dir):
                if file.endswith(".jpg") or file.endswith(".mp4") or file.endswith(".png") or file.endswith(".jpeg") or file.endswith(".gif"):
                    media_file = discord.File(tmp_download_dir+"/"+file)
                    size = os.path.getsize(tmp_download_dir+"/"+file)
                    media_files.append({"file": media_file, "size": size})
            self.bot.log.info("Downloaded "+str(len(media_files))+" files from @"+str(profile.username)+"'s story", guild)
            os.system("rm -rf "+tmp_download_dir+"/*")
            # create an embed message with the story
            embed = discord.Embed(
                title=str(profile.full_name),
                url="https://www.instagram.com/"+str(profile.username),
                description="Type: Story\n",
                color=self.bot.default_color,
                )
            embed.set_thumbnail(url=profile.profile_pic_url)
            return media_files, embed
        except instaloader.exceptions.InstaloaderException as e:
            embed = discord.Embed(
                    title="Sorry! There is some problem.",
                    description="A exception occured while trying to download the story. Possibly the user is private or the story doesn't exist or the user @"+str(profile.username)+" doesn't have any stories.",
                    color=self.bot.default_color,
                    )
            return None, embed

    @commands.command( name="watch_channel", description="Set the channel to watch for instagram links.")
    async def watchchannel(self, context: Context, channel: discord.TextChannel = None):
        '''Set the channel to watch for instagram links'''
        if channel == None:
            channel = context.channel
        if str(context.guild.id) not in self.channels_to_watch.keys():
            self.channels_to_watch[str(context.guild.id)] = list()
        self.channels_to_watch[str(context.guild.id)].append(str(channel.id))
        self.save_channel_watch_list()
        embed = discord.Embed(
                title="Instagram channel set",
                description="I will watch for instagram links in "+channel.mention+".",
                color=self.bot.default_color,
                )
        await context.send(embed=embed)
        self.bot.log.info("Added channel "+str(channel.id)+" to watch for instagram links.", context.guild)
    
    @commands.command( name="unwatch_channel", description="Unset the channel to watch for instagram links.")
    async def unwatchchannel(self, context: Context, channel: discord.TextChannel = None): 
        '''Unset the channel to watch for instagram links'''
        if channel == None:
            channel = context.channel
        if str(context.guild.id) not in self.channels_to_watch.keys():
            self.channels_to_watch[str(context.guild.id)] = list()
        self.channels_to_watch[str(context.guild.id)].remove(str(channel.id))
        self.save_channel_watch_list()
        embed = discord.Embed(
                title="Instagram channel unset",
                description="I will remove "+channel.mention+" from my watch list for instagram links.",
                color=self.bot.default_color,
                )
        await context.send(embed=embed)
        self.bot.log.info("Removed channel "+str(channel.id)+" from watch for instagram links.", context.guild)

    @commands.command( name="watch_list", description="Show the list of channels to watch for instagram links.")
    async def watchlist(self, context: Context):
        '''Show the list of channels to watch for instagram links'''
        if str(context.guild.id) in self.channels_to_watch.keys():
            watch_list = self.channels_to_watch.get(str(context.guild.id), [])
            channels = [context.guild.get_channel(int(channel)) for channel in watch_list]
            embed = discord.Embed(
                title="Instagram watch list",
                description="I am watching for instagram links in the following channels: \n"+", ".join([channel.mention for channel in channels if channel is not None]),
                color=self.bot.default_color,
                )
            await context.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Instagram watch list",
                description="I am not watching for instagram links in any channel in this server.",
                color=self.bot.default_color,
                )
            await context.send(embed=embed)
    
    def load_channel_watch_list(self):
        # load the channels to watch for instagram links
        if os.path.exists(self.bot.data_dir):
            guilds = os.listdir(self.bot.data_dir)
            guilds = [guild for guild in guilds if os.path.isdir(os.path.join(self.bot.data_dir, guild))]
            for guild_id in guilds:
                if os.path.exists(os.path.join(self.bot.data_dir, guild_id, "instagram_watch_list.yml")):
                    with open(os.path.join(self.bot.data_dir, guild_id, "instagram_watch_list.yml"), 'r') as file:
                        watch_list = yaml.safe_load(file)
                        if watch_list is not None:
                            if guild_id not in self.channels_to_watch.keys():
                                self.channels_to_watch[guild_id] = list()
                            self.channels_to_watch[guild_id].extend(watch_list.get("channels", []))
                    self.bot.log.info("Loaded watch list for guild "+str(guild_id))
                else:
                    self.bot.log.info("No watch list found for guild "+str(guild_id))
    
    def save_channel_watch_list(self):
        # save the channels to watch for instagram links
        if os.path.exists(self.bot.data_dir):
            guilds = os.listdir(self.bot.data_dir)
            guilds = [guild for guild in guilds if os.path.isdir(os.path.join(self.bot.data_dir, guild))]
            for guild_id in guilds:
                if guild_id in self.channels_to_watch.keys():
                    with open(os.path.join(self.bot.data_dir, guild_id, "instagram_watch_list.yml"), 'w+') as file:
                        yaml.dump({"channels": self.channels_to_watch[guild_id]}, file)
                    self.bot.log.info("Saved watch list for guild "+str(guild_id))
    
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
        # load the session from file
        session_dir = os.path.join(self.bot.data_dir, str(guild.id),"session")
        if os.path.exists(session_dir):
            session_file = os.path.join(session_dir, os.listdir(session_dir)[0])
            username = os.listdir(session_dir)[0].split(".")[0]
            self.loader.load_session_from_file(username, session_file)
            self.bot.log.info("Loaded session of "+str(username)+" for guild "+str(guild.name), guild)
        else:
            self.bot.log.warning("No session found for guild "+str(guild.name), guild)
    
    def save_session(self, guild : discord.Guild):
        # save the session to file
        session_dir = os.path.join(self.bot.data_dir, str(guild.id),"session")
        self.clear_session(guild)
        username = self.loader.test_login()
        session_file = os.path.join(session_dir, f"{username}.session")
        self.loader.save_session_to_file(session_file)
        self.bot.log.info("Saved session of "+str(username)+" for guild "+str(guild.name), guild)
    
    def clear_session(self, guild : discord.Guild):
        # clear the session
        session_dir = os.path.join(self.bot.data_dir, str(guild.id),"session")
        if os.path.exists(session_dir):
            os.system("rm -rf "+session_dir)
            self.bot.log.info("Cleared session for guild "+str(guild.name), guild)
        else:
            self.bot.log.info("No existing session found for guild "+str(guild.name), guild)


async def setup(bot):
    await bot.add_cog(Instagram(bot))