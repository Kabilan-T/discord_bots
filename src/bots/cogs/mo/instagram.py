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
import discord
import requests
from discord.ext import commands
from discord.ext.commands import Context
import instaloader

tmp_download_dir = "tmp"
instagram_regex = r'\bhttps?:\/\/(?:www\.)?instagram\.com\/(?:[a-zA-Z0-9_\.]+\/)?[a-zA-Z0-9_\.\/-]+\/?\b'

class Instagram(commands.Cog, name="Instagram"):
    def __init__(self, bot):
        self.bot = bot
        self.loader = instaloader.Instaloader()
        # channels to watch for instagram links
        self.channels_to_watch = dict()
        self.load_channel_watch_list()
        # self.channels_to_watch.append(1183051684767871076) # axiom server - sauce-deck channel
        # get the instagram credentials
        self.is_credentials_provided = self._get_credentials()
        # login to instagram
        if self.is_credentials_provided:
            self._login_to_instagram()

    @commands.command( name="bio", description="Get the bio of a user.")
    async def bio(self, context: Context, username: str):
        '''Get the bio of a user'''
        await self.send_bio(context.reply, username, context.guild)

    @commands.command( name="show", description="Download a post from instagram.")
    async def show(self, context: Context, message: str):
        '''Download a media from instagram and show it'''
        match = re.match(instagram_regex, message)
        if match is not None:
            url = match.group()
            await self.send_media(context.reply, url, context.guild)

    @commands.command( name="set_channel", description="Set the channel to watch for instagram links.")
    async def setchannel(self, context: Context, channel: discord.TextChannel = None):
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

    @commands.command( name="unset_channel", description="Unset the channel to watch for instagram links.")
    async def unsetchannel(self, context: Context, channel: discord.TextChannel = None):
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



    @commands.Cog.listener()
    async def on_message(self, message):
        ''' Watch for instagram links and send the media'''
        if str(message.channel.id) in self.channels_to_watch.get(str(message.guild.id), []) and message.author.bot == False and message.content != "":
            match = re.match(instagram_regex, message.content)
            if match is not None:
                instagram_url = match.group()
                if len(instagram_url.split("/")) == 4:
                    # Link is of a profile - get the bio
                    self.bot.log.info("Got a link of a profile from "+message.guild.name+" #"+message.channel.name+" sent by @"+message.author.name)
                    await self.send_bio(message.reply, instagram_url, message.guild)
                elif len(instagram_url.split("/")) >= 5:
                    # Link is of a media - get the media and send it
                    self.bot.log.info("Got a link of a media from "+message.guild.name+" #"+message.channel.name+" sent by @"+message.author.name)
                    await self.send_media(message.reply, instagram_url, message.guild)
                else:
                    return

    async def send_bio(self, replier, username, guild=None):
        # send the bio of a user
        if username.startswith("@"):
            username = username[1:]
        elif username.startswith("https://www.instagram.com/"):
            username = username.split("/")[-1]
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
            self.bot.log.error("Failed to send bio of "+str(username), guild)
    
    async def send_media(self, replier, url, guild=None):
        # download a media from instagram url and send it
        if url.split("/")[3] == "p":
            await self.send_post(replier, url, guild)
        elif url.split("/")[3] == "reel":
            await self.send_reel(replier, url, guild)
        elif url.split("/")[3] == "stories":
            await self.send_stories(replier, url, guild)

    async def send_post(self, replier, url, guild=None):
        # send a post
        try:
            #Find the post from the url
            shortcode = url.split("/")[-1]  # (https://www.instagram.com/p/<shortcode>)
            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
            # Download the post
            self.loader.download_post(post, target=tmp_download_dir)
            media_files = [discord.File(tmp_download_dir+"/"+file) for file in os.listdir(os.getcwd()+"/"+tmp_download_dir)
                            if file.endswith(".jpg") or file.endswith(".mp4") or file.endswith(".png") or file.endswith(".jpeg") or file.endswith(".gif")]
            os.system("rm -rf "+tmp_download_dir+"/*")
            # Send the post with caption and likes as embed message
            if post.caption is not None:
                short_caption = post.caption.split("\n")[0] if len(post.caption.split("\n")[0]) < 50  else post.caption.split("\n")[0][:50]+"..."
            else:
                short_caption = "No caption"
            embed = discord.Embed(
                title=str(post.owner_profile.full_name),
                url="https://www.instagram.com/"+str(post.owner_profile.username),
                description="Caption: "+str(short_caption)+"\nType: Post ("+str(len(media_files))+" files)\nLikes: "+str(post.likes)+"\n",
                color=self.bot.default_color,
            )
            embed.set_thumbnail(url=post.owner_profile.profile_pic_url)
            await replier(embed=embed, files=media_files)
            self.bot.log.info("Downloaded and sent "+str(len(media_files))+" files from @"+str(post.owner_profile.username)+"'s post ", guild)
        except instaloader.exceptions.InstaloaderException as e:
            embed = discord.Embed(
                    title="Sorry! There is some problem.",
                    description="A exception occured while trying to download the post. Possibly the user is private or the post doesn't exist.",
                    color=self.bot.default_color,
                    )
            await replier(embed=embed)
            self.bot.log.error("Failed to send post from "+str(url), guild)
            self.bot.log.error("Exception raised by instaloader: "+str(e), guild)

    async def send_reel(self, replier, url, guild=None):
        # send a reel
        try:
            #Find the reel from the url
            shortcode = url.split("/")[-1]  # (https://www.instagram.com/reel/<shortcode>)
            reel = instaloader.Post.from_shortcode(self.loader.context, shortcode)
            # Download the reel
            self.loader.download_post(reel, target=tmp_download_dir)
            media_files = [discord.File(tmp_download_dir+"/"+file) for file in os.listdir(os.getcwd()+"/"+tmp_download_dir)
                            if file.endswith(".mp4")]   # Reels are always mp4. jpg is for thumbnail
            os.system("rm -rf "+tmp_download_dir+"/*")
            # Send the reel with caption and likes as embed message
            if reel.caption is not None:
                short_caption = reel.caption.split("\n")[0] if len(reel.caption.split("\n")[0]) < 50  else reel.caption.split("\n")[0][:50]+"..."
            else:
                short_caption = "No caption"
            embed = discord.Embed(
                title=str(reel.owner_profile.full_name),
                url="https://www.instagram.com/"+str(reel.owner_profile.username),
                description="Caption: "+str(short_caption)+"\nType: Reel \nLikes: "+str(reel.likes)+"\n",
                color=self.bot.default_color,
            )
            embed.set_thumbnail(url=reel.owner_profile.profile_pic_url)
            await replier(embed=embed, files=media_files)
            self.bot.log.info("Downloaded and sent "+str(len(media_files))+" files from @"+str(reel.owner_profile.username)+"'s reel ", guild)
        except instaloader.exceptions.InstaloaderException:
            embed = discord.Embed(
                    title="Sorry! There is some problem. :sweat:",
                    description="A exception occured while trying to download the reel. Possibly the user is private or the reel doesn't exist.",
                    color=self.bot.default_color,
                    )
            await replier(embed=embed)
            self.bot.log.error("Failed to send reel from "+str(url), guild)
            self.bot.log.error("Exception raised by instaloader: "+str(e), guild)

    async def send_stories(self, replier, url, guild=None):
        # stories requires
        if self.is_credentials_provided == False:
            embed = discord.Embed(
                title="Sorry! There is some problem. :sweat:",
                description="Stories can be downloaded only if the bot is logged in. There is no login credentials provided to log in to instagram.",
                color=self.bot.default_color,
                )
            await replier(embed=embed)
            return
        else:
            if self._login_to_instagram() == False:
                embed = discord.Embed(
                    title="Sorry! There is some problem. :sweat:",
                    description="I tried to log in to instagram but unfortunately I couldn't. Try again later.",
                    color=self.bot.default_color,
                    )
                await replier(embed=embed)
                return
        # send a story
        try:
            profile = instaloader.Profile.from_username(self.loader.context, url.split("/")[4])
            # Download the story
            self.loader.download_stories([profile.userid],  filename_target=tmp_download_dir)
            # if there is a video and image with same name, remove the image
            media_files = list()
            for file in os.listdir(os.getcwd()+"/"+tmp_download_dir):
                if file.endswith(".jpg") or file.endswith(".mp4") or file.endswith(".png") or file.endswith(".jpeg") or file.endswith(".gif"):
                    if file.split(".")[0]+".mp4" not in [file.filename for file in media_files]:
                        media_files.append(discord.File(tmp_download_dir+"/"+file))
            os.system("rm -rf "+tmp_download_dir+"/*")
            # Send the story 
            embed = discord.Embed(
                title=str(profile.full_name),
                url="https://www.instagram.com/"+str(profile.username),
                description="Type: Story ("+str(len(media_files))+" files)\n",
                color=self.bot.default_color,
            )
            embed.set_thumbnail(url=profile.profile_pic_url)
            await replier(embed=embed, files=media_files)
            self.bot.log.info("Downloaded and sent "+str(len(media_files))+" files from @"+str(profile.username)+"'s story", guild)
        except instaloader.exceptions.InstaloaderException:
            embed = discord.Embed(
                    title="Sorry! There is some problem.",
                    description="A exception occured while trying to download the story. Possibly the user is private or the story doesn't exist.",
                    color=self.bot.default_color,
                    )
            await replier(embed=embed)
            self.bot.log.error("Failed to send story from "+str(url), guild)
            self.bot.log.error("Exception raised by instaloader: "+str(e), guild)

    def _get_credentials(self):
        # get the instagram credentials
        if os.environ.get("INSTAGRAM_USERNAME") != None and os.environ.get("INSTAGRAM_PASSWORD") != None:
            self._username = os.environ.get("INSTAGRAM_USERNAME")
            self._password = os.environ.get("INSTAGRAM_PASSWORD")
            self.bot.log.info("Instagram credentials are provided")
            return True
        else:
            self.bot.log.info("Instagram credentials are not provided")
            return False
    
    def _login_to_instagram(self):
        # check if already logged in
        if self.loader.context.is_logged_in == True:
            self.bot.log.info("Already logged in to instagram.")
            return True
        # try to log in
        try:
            self.bot.log.info("Trying to log in to instagram ...")
            self.loader.login(self._username, self._password)
            # check if logged in
            if self.loader.test_login() == self._username:
                self.bot.log.info("Logged in to instagram successfully.")
                return True
            else:
                self.bot.log.error("Failed to log in to instagram.")
                return False
        except instaloader.exceptions.BadCredentialsException:
            self.bot.log.error("Failed to log in to instagram. Bad credentials.")
            return False
        
    def load_channel_watch_list(self):
        # load the channels to watch for instagram links
        if os.path.exists(self.bot.data_dir):
            guilds = os.listdir(self.bot.data_dir)
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
            for guild_id in guilds:
                if guild_id in self.channels_to_watch.keys():
                    with open(os.path.join(self.bot.data_dir, guild_id, "instagram_watch_list.yml"), 'w+') as file:
                        yaml.dump({"channels": self.channels_to_watch[guild_id]}, file)
                    self.bot.log.info("Saved watch list for guild "+str(guild_id))


async def setup(bot):
    await bot.add_cog(Instagram(bot))