#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Command related to instagram and its API'''

#-------------------------------------------------------------------------------

import os
import discord
from discord.ext import commands
from discord.ext.commands import Context
import instaloader

temp_download_dir = "downloads"

class Instagram(commands.Cog, name="Instagram"):
    def __init__(self, bot):
        self.bot = bot
        # Load proxy list from config file proxy.txt
        proxy_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "proxy.txt")
        if os.path.exists(proxy_dir):
            with open(proxy_dir, "r") as f:
                self.proxy_list = f.read().split("\n")
            print("Proxy list loaded. "+str(len(self.proxy_list))+" proxies found.")
        else:
            print("Proxy list not found. Proxy will not be used.")
            self.proxy_list = None

        # channels to watch for instagram links
        self.channels_to_watch = list()
        self.channels_to_watch.append(1183051684767871076) # axiom server - sauce-deck channel
        self.channels_to_watch.append(1186341011350360167) # Hello World server - general channel


    @commands.hybrid_command( name="bio", description="Get the bio of a user.")
    async def bio(self, context: Context, username: str):
        # Get the bio of a user
        await self.send_bio(context.reply, username)

    @commands.hybrid_command( name="set_channel", description="Set the channel to watch for instagram links.")
    async def set_channel(self, context: Context, channel: discord.TextChannel):
        # Set the channel to watch for instagram links
        self.channels_to_watch.append(channel.id)
        await context.send("Instagram channel set to "+channel.mention+".")

    @commands.hybrid_command( name="show", description="Download a post from instagram.")
    async def show(self, context: Context, url: str):
        # Download a media from instagram and show it
        await self.send_media(context.reply, url)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id in self.channels_to_watch and message.author.bot == False and message.content != "":
            if str("https://www.instagram.com/") in message.content:
                if len(message.content.split("/")) == 4:
                    # Link is of a profile - get the bio
                    await self.send_bio(message.reply, message.content)
                elif len(message.content.split("/")) >= 5:
                    # Link is of a media - get the media and send it
                    await self.send_media(message.reply, message.content)
                else:
                    return
                
    def setup_proxy(self):
        # setup proxy form proxy list
        if self.proxy_list != None:
            proxy = self.proxy_list[0]
            os.environ["http_proxy"] = "http://"+proxy
            os.environ["https_proxy"] = "http://"+proxy
            print("Proxy set to "+proxy)
            self.proxy_list.remove(proxy)

    def remove_proxy(self):
        if os.environ.get("http_proxy") != None and os.environ.get("https_proxy") != None:
            os.environ["http_proxy"] = ""
            os.environ["https_proxy"] = ""
            print("Proxy removed")
                
    def login(self,L):
        # login to instagram if login credentials are provided
        if os.environ.get("INSTAGRAM_USERNAME") != None and os.environ.get("INSTAGRAM_PASSWORD") != None:
            username = os.environ.get("INSTAGRAM_USERNAME")
            password = os.environ.get("INSTAGRAM_PASSWORD")
            try:
                print("Trying to login to instagram...")
                L.login(username, password)
                if L.test_login() == username:
                    print("Instagram login successful. Logged in as "+username)
                    return True
                else:
                    print("Instagram login failed. Please check your credentials.")
                    return False
            except Exception as e:
                print("couldn't login to instagram. Error: "+str(e))
                return False
        else:
            print("No instagram credentials provided. Login failed.")
            return False

    async def send_bio(self, reply_function, username):
        # send the bio of a user
        if username.startswith("@"):
            username = username[1:]
        elif username.startswith("https://www.instagram.com/"):
            username = username.split("/")[-1]
        try:
            self.setup_proxy()
            L = instaloader.Instaloader()
            
            print(L.context._session.proxies.__str__())
            #self.login(L)
            profile = instaloader.Profile.from_username(L.context, username)
            self.remove_proxy()
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
        except instaloader.exceptions.InstaloaderException:
            self.remove_proxy()
            embed = discord.Embed(
                    title="Sorry! There is some problem.",
                    description="Possibly the username is wrong or doesn't exist.",
                    color=0xBEBEFE,
                    )
            await reply_function(embed=embed)
    
    async def send_media(self, reply_function, url):
        # download a media from instagram url and send it
        if url.split("/")[3] == "p":
            await self.send_post(reply_function, url)
        elif url.split("/")[3] == "reel":
            await self.send_reel(reply_function, url)
        elif url.split("/")[3] == "stories":
            await self.send_stories(reply_function, url)

    async def send_post(self, reply_function, url):
        # send a post
        try:
            self.setup_proxy()
            L = instaloader.Instaloader()
            #self.login(L)
            #Find the post from the url
            shortcode = url.split("/")[-2]  # (https://www.instagram.com/p/<shortcode>/<post_id>)
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            # Download the post
            L.download_post(post, target=temp_download_dir)
            self.remove_proxy()
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
        except instaloader.exceptions.InstaloaderException:
            self.remove_proxy()
            embed = discord.Embed(
                    title="Sorry! There is some problem.",
                    description="Possibly the user is private or the post doesn't exist.",
                    color=0xBEBEFE,
                    )
            await reply_function(embed=embed)

    async def send_reel(self, reply_function, url):
        # send a reel
        try:
            self.setup_proxy()
            L = instaloader.Instaloader()
            #self.login(L)
            #Find the post from the url
            shortcode = url.split("/")[-2]  # (https://www.instagram.com/reel/<shortcode>/<post_id>)
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            # Download the post
            L.download_post(post, target=temp_download_dir)
            self.remove_proxy()
            media_files = [discord.File(temp_download_dir+"/"+file) for file in os.listdir(os.getcwd()+"/"+temp_download_dir)
                            if file.endswith(".mp4")]   # Reels are always mp4. jpg is for thumbnail
            os.system("rm -rf "+temp_download_dir+"/*")
            # Send the post with caption and likes as embed message
            short_caption = post.caption.split("\n")[0] if len(post.caption.split("\n")[0]) < 50  else post.caption.split("\n")[0][:50]+"..."
            embed = discord.Embed(
                title=str(post.owner_profile.full_name),
                url="https://www.instagram.com/"+str(post.owner_profile.username),
                description="Caption: "+str(short_caption)+"\nType: Reel \nLikes: "+str(post.likes)+"\n",
                color=0xBEBEFE,
            )
            embed.set_thumbnail(url=post.owner_profile.profile_pic_url)
            await reply_function(embed=embed, files=media_files)
        except instaloader.exceptions.InstaloaderException:
            self.remove_proxy()
            embed = discord.Embed(
                    title="Sorry! There is some problem.",
                    description="Possibly the user is private or the post doesn't exist.",
                    color=0xBEBEFE,
                    )
            await reply_function(embed=embed)

    async def send_stories(self, reply_function, url):
        # send a story
        try:
            # TODO: Yet to be implemented
            embed = discord.Embed(
                    title="Sorry! Stories are not yet implemented.",
                    description=" Hopefully it will be implemented soon.",
                    color=0xBEBEFE,
                    )
            await reply_function(embed=embed)
        except instaloader.exceptions.InstaloaderException:
            embed = discord.Embed(
                    title="Sorry! There is some problem.",
                    description="Possibly the user is private or the post doesn't exist.",
                    color=0xBEBEFE,
                    )
            await reply_function(embed=embed)
    
async def setup(bot):
    await bot.add_cog(Instagram(bot))