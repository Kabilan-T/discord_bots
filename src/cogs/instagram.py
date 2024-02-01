#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Command related to instagram and its API'''

#-------------------------------------------------------------------------------

import os
import discord
import requests
from discord.ext import commands
from discord.ext.commands import Context
import instaloader

temp_download_dir = "downloads"
proxy_list = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "proxies.txt")

class Instagram(commands.Cog, name="Instagram"):
    def __init__(self, bot):
        self.bot = bot
        self.loader = instaloader.Instaloader()
        # channels to watch for instagram links
        self.channels_to_watch = list()
        self.channels_to_watch.append(1183051684767871076) # axiom server - sauce-deck channel
        # get the instagram credentials
        self.is_credentials_provided = self._get_credentials()
         # read the proxies
        with open(proxy_list, "r") as file:
            self.proxies = [line.strip() for line in file.readlines()]
        # login to instagram
        if self.is_credentials_provided:
            self._login_to_instagram()

    @commands.hybrid_command( name="bio", description="Get the bio of a user.")
    async def bio(self, context: Context, username: str):
        '''Get the bio of a user'''
        await self.send_bio(context.reply, username)

    @commands.hybrid_command( name="set_channel", description="Set the channel to watch for instagram links.")
    async def set_channel(self, context: Context, channel: discord.TextChannel = None):
        '''Set the channel to watch for instagram links'''
        if channel == None:
            channel = context.channel
        self.channels_to_watch.append(channel.id)
        embed = discord.Embed(
                title="Instagram channel set",
                description="I will watch for instagram links in "+channel.mention+".",
                color=0xBEBEFE,
                )
        await context.send(embed=embed)
        self.bot.logger.info("Added channel "+str(channel.id)+" to watch for instagram links.")

    @commands.hybrid_command( name="unset_channel", description="Unset the channel to watch for instagram links.")
    async def unset_channel(self, context: Context, channel: discord.TextChannel = None):
        '''Unset the channel to watch for instagram links'''
        if channel == None:
            channel = context.channel
        self.channels_to_watch.remove(channel.id)
        embed = discord.Embed(
                title="Instagram channel unset",
                description="I will remove "+channel.mention+" from my watch list for instagram links.",
                color=0xBEBEFE,
                )
        await context.send(embed=embed)
        self.bot.logger.info("Removed channel "+str(channel.id)+" from watch for instagram links.")

    @commands.hybrid_command( name="show", description="Download a post from instagram.")
    async def show(self, context: Context, url: str):
        '''Download a media from instagram and show it'''
        await self.send_media(context.reply, url)

    @commands.Cog.listener()
    async def on_message(self, message):
        ''' Watch for instagram links and send the media'''
        if message.channel.id in self.channels_to_watch and message.author.bot == False and message.content != "":
            if str("https://www.instagram.com/") in message.content:
                if len(message.content.split("/")) == 4:
                    # Link is of a profile - get the bio
                    self.bot.logger.info("Got a link of a profile from "+message.guild.name+" #"+message.channel.name+" sent by @"+message.author.name)
                    await self.send_bio(message.reply, message.content)
                elif len(message.content.split("/")) >= 5:
                    # Link is of a media - get the media and send it
                    self.bot.logger.info("Got a link of a media from "+message.guild.name+" #"+message.channel.name+" sent by @"+message.author.name)
                    await self.send_media(message.reply, message.content)
                else:
                    return

    async def send_bio(self, reply_function, username):
        # send the bio of a user
        if username.startswith("@"):
            username = username[1:]
        elif username.startswith("https://www.instagram.com/"):
            username = username.split("/")[-1]
        if self.setup_proxy() == False:
            embed = discord.Embed(
                    title="Sorry! There is some problem. :sweat:",
                    description="I couldn't set up proxy to get the bio.",
                    color=0xBEBEFE,
                    )
            await reply_function(embed=embed)
            return
        try:    
            profile = instaloader.Profile.from_username(self.loader.context, username)
            embed = discord.Embed(
                    title=str(profile.full_name),
                    url="https://www.instagram.com/"+str(profile.username),
                    description=profile.biography,
                    color=0xBEBEFE,
                    )
            embed.set_thumbnail(url=profile.profile_pic_url)
            embed.add_field(name="Followers", value=str(profile.followers), inline=True)
            embed.add_field(name="Following", value=str(profile.followees), inline=True)
            embed.add_field(name="Posts", value=str(profile.mediacount), inline=True)
            await reply_function(embed=embed)
            self.bot.logger.info("Sent bio of @"+str(profile.username))
        except instaloader.exceptions.InstaloaderException:
            embed = discord.Embed(
                    title="Sorry! There is some problem. :sweat:",
                    description="Possibly the username is wrong or doesn't exist.",
                    color=0xBEBEFE,
                    )
            await reply_function(embed=embed)
            self.bot.logger.error("Failed to send bio of "+str(username))
    
    async def send_media(self, reply_function, url):
        # download a media from instagram url and send it
        if self.setup_proxy() == False:
            embed = discord.Embed(
                    title="Sorry! There is some problem. :sweat:",
                    description="I couldn't set up proxy to download the media.",
                    color=0xBEBEFE,
                    )
            await reply_function(embed=embed)
            return
        if url.split("/")[3] == "p":
            await self.send_post(reply_function, url)
        elif url.split("/")[3] == "reel":
            await self.send_reel(reply_function, url)
        elif url.split("/")[3] == "stories":
            await self.send_stories(reply_function, url)

    async def send_post(self, reply_function, url):
        # send a post
        try:
            #Find the post from the url
            shortcode = url.split("/")[-2]  # (https://www.instagram.com/p/<shortcode>/<post_id>)
            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
            # Download the post
            self.loader.download_post(post, target=temp_download_dir)
            media_files = [discord.File(temp_download_dir+"/"+file) for file in os.listdir(os.getcwd()+"/"+temp_download_dir)
                            if file.endswith(".jpg") or file.endswith(".mp4") or file.endswith(".png") or file.endswith(".jpeg") or file.endswith(".gif")]
            os.system("rm -rf "+temp_download_dir+"/*")
            # Send the post with caption and likes as embed message
            short_caption = post.caption.split("\n")[0] if len(post.caption.split("\n")[0]) < 50  else post.caption.split("\n")[0][:50]+"..."
            embed = discord.Embed(
                title=str(post.owner_profile.full_name),
                url="https://www.instagram.com/"+str(post.owner_profile.username),
                description="Caption: "+str(short_caption)+"\nType: Post ("+str(len(media_files))+" files)\nLikes: "+str(post.likes)+"\n",
                color=0xBEBEFE,
            )
            embed.set_thumbnail(url=post.owner_profile.profile_pic_url)
            await reply_function(embed=embed, files=media_files)
            self.bot.logger.info("Downloaded and sent "+str(len(media_files))+" files from @"+str(post.owner_profile.username)+"'s post "+str(post.mediaid))
        except instaloader.exceptions.InstaloaderException:
            embed = discord.Embed(
                    title="Sorry! There is some problem.",
                    description="Possibly the user is private or the post doesn't exist.",
                    color=0xBEBEFE,
                    )
            await reply_function(embed=embed)
            self.bot.logger.error("Failed to send post from "+str(url))

    async def send_reel(self, reply_function, url):
        # send a reel
        try:
            #Find the reel from the url
            shortcode = url.split("/")[-2]  # (https://www.instagram.com/reel/<shortcode>/<post_id>)
            reel = instaloader.Post.from_shortcode(self.loader.context, shortcode)
            # Download the reel
            self.loader.download_post(reel, target=temp_download_dir)
            media_files = [discord.File(temp_download_dir+"/"+file) for file in os.listdir(os.getcwd()+"/"+temp_download_dir)
                            if file.endswith(".mp4")]   # Reels are always mp4. jpg is for thumbnail
            os.system("rm -rf "+temp_download_dir+"/*")
            # Send the reel with caption and likes as embed message
            short_caption = reel.caption.split("\n")[0] if len(reel.caption.split("\n")[0]) < 50  else reel.caption.split("\n")[0][:50]+"..."
            embed = discord.Embed(
                title=str(reel.owner_profile.full_name),
                url="https://www.instagram.com/"+str(reel.owner_profile.username),
                description="Caption: "+str(short_caption)+"\nType: Reel \nLikes: "+str(reel.likes)+"\n",
                color=0xBEBEFE,
            )
            embed.set_thumbnail(url=reel.owner_profile.profile_pic_url)
            await reply_function(embed=embed, files=media_files)
            self.bot.logger.info("Downloaded and sent "+str(len(media_files))+" files from @"+str(reel.owner_profile.username)+"'s reel "+str(reel.mediaid))
        except instaloader.exceptions.InstaloaderException:
            embed = discord.Embed(
                    title="Sorry! There is some problem. :sweat:",
                    description="Possibly the user is private or the reel doesn't exist.",
                    color=0xBEBEFE,
                    )
            await reply_function(embed=embed)
            self.bot.logger.error("Failed to send reel from "+str(url))

    async def send_stories(self, reply_function, url):
        # stories requires
        if self.is_credentials_provided == False:
            embed = discord.Embed(
                title="Sorry! There is some problem. :sweat:",
                description="Stories can be downloaded only if the bot is logged in. There is no login credentials provided to log in to instagram.",
                color=0xBEBEFE,
                )
            await reply_function(embed=embed)
            return
        else:
            if self._login_to_instagram() == False:
                embed = discord.Embed(
                    title="Sorry! There is some problem. :sweat:",
                    description="I tried to log in to instagram but unfortunately I couldn't. Try again later.",
                    color=0xBEBEFE,
                    )
                await reply_function(embed=embed)
                return
        # send a story
        try:
            profile = instaloader.Profile.from_username(self.loader.context, url.split("/")[4])
            # Download the story
            self.loader.download_stories([profile.userid],  filename_target=temp_download_dir)
            # if there is a video and image with same name, remove the image
            media_files = list()
            for file in os.listdir(os.getcwd()+"/"+temp_download_dir):
                if file.endswith(".jpg") or file.endswith(".mp4") or file.endswith(".png") or file.endswith(".jpeg") or file.endswith(".gif"):
                    if file.split(".")[0]+".mp4" not in [file.filename for file in media_files]:
                        media_files.append(discord.File(temp_download_dir+"/"+file))
            os.system("rm -rf "+temp_download_dir+"/*")
            # Send the story 
            embed = discord.Embed(
                title=str(profile.full_name),
                url="https://www.instagram.com/"+str(profile.username),
                description="Type: Story ("+str(len(media_files))+" files)\n",
                color=0xBEBEFE,
            )
            embed.set_thumbnail(url=profile.profile_pic_url)
            await reply_function(embed=embed, files=media_files)
            self.bot.logger.info("Downloaded and sent "+str(len(media_files))+" files from @"+str(profile.username)+"'s story")
        except instaloader.exceptions.InstaloaderException:
            embed = discord.Embed(
                    title="Sorry! There is some problem.",
                    description="Possibly the user is private or the reel doesn't exist.",
                    color=0xBEBEFE,
                    )
            await reply_function(embed=embed)
            self.bot.logger.error("Failed to send story from "+str(url))

    def _get_credentials(self):
        # get the instagram credentials
        if os.environ.get("INSTAGRAM_USERNAME") != None and os.environ.get("INSTAGRAM_PASSWORD") != None:
            self._username = os.environ.get("INSTAGRAM_USERNAME")
            self._password = os.environ.get("INSTAGRAM_PASSWORD")
            self.bot.logger.info("Instagram credentials are provided")
            return True
        else:
            self.bot.logger.error("Instagram credentials are not provided")
            return False
    
    def _login_to_instagram(self):
        # check if already logged in
        if self.loader.context.is_logged_in == True:
            self.bot.logger.info("Already logged in to instagram.")
            return True
        if self.setup_proxy() == False:
            self.bot.logger.error("Proxy is not set up. Can't log in to instagram.")
            return False
        # try to log in
        try:
            self.bot.logger.info("Trying to log in to instagram ...")
            self.loader.login(self._username, self._password)
            # check if logged in
            if self.loader.test_login() == self._username:
                self.bot.logger.info("Logged in to instagram successfully.")
                return True
            else:
                self.bot.logger.error("Failed to log in to instagram.")
                return False
        except instaloader.exceptions.BadCredentialsException:
            self.bot.logger.error("Failed to log in to instagram. Bad credentials.")
            return False
    
    def _setup_proxy(self, proxy):
        # set up proxy
        try:
            self.bot.logger.info("Trying to set up proxy with "+str(proxy))
            proxies = {"http": "http://"+str(proxy), 
                       "https": "https://"+str(proxy)}
            session = requests.Session()
            session.proxies.update(proxies)
            # os.environ["HTTP_PROXY"] = "http://" + str(self._username) + ":" + str(self._password) + "@" + proxy
            # os.environ["HTTPS_PROXY"] = "https://" + str(self._username) + ":" + str(self._password) + "@" + proxy

            # test the proxy
            response = requests.get("https://www.google.com/", proxies=proxies, timeout=5)
            print(response.json(), response.status_code)
            if response.status_code != 200:
                self.bot.logger.error("Proxy is not working.")
                return False
            else:
                self.bot.logger.info("Proxy is working.")
            # set up the proxy
            self.loader.context._session = session
            self.bot.logger.info("Proxy set up successfully.")
            
        except Exception as e:
            self.bot.logger.error("Failed to set up proxy. "+str(e))
            return False
    
    def setup_proxy(self):
        # Rotate the proxies
        proxy = self.proxies.pop(0)
        if proxy != None:
            if self._setup_proxy(proxy) == False:
                self.bot.logger.error("Trying next proxy.")
                return self.setup_proxy()
            else:
                return True 
        else:
            self.bot.logger.error("No proxies left to try.")
            return False
    
async def setup(bot):
    await bot.add_cog(Instagram(bot))