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
        self.channel_to_watch = None
        self.loader = instaloader.Instaloader()
        proxy = "246.60.163.237:8080"

        self.loader.context._session.proxies = {"http": "http://" + proxy, "https": "https://" + proxy}
        print("using proxy :- https://" + proxy)


    @commands.hybrid_command( name="bio", description="Get the bio of a user.")
    async def bio(self, context: Context, username: str):
        # Get the bio of a user
        await self.send_bio(context.reply, username)

    @commands.hybrid_command( name="set_channel", description="Set the channel to watch for instagram links.")
    async def set_channel(self, context: Context, channel: discord.TextChannel):
        # Set the channel to watch for instagram links
        self.channel_to_watch = channel
        await context.send("Instagram channel set to "+channel.mention+".")

    @commands.hybrid_command( name="show", description="Download a post from instagram.")
    async def show(self, context: Context, url: str):
        # Download a media from instagram and show it
        await self.send_media(context.reply, url)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel == self.channel_to_watch and message.author.bot == False and message.content != "":
            if str("https://www.instagram.com/") in message.content:
                if len(message.content.split("/")) == 4:
                    # Link is of a profile - get the bio
                    await self.send_bio(message.reply, message.content)
                elif len(message.content.split("/")) >= 5:
                    # Link is of a media - get the media and send it
                    await self.send_media(message.reply, message.content)
                else:
                    return

    async def send_bio(self, reply_function, username):
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
                    color=0xBEBEFE,
                    )
            embed.set_thumbnail(url=profile.profile_pic_url)
            embed.add_field(name="Followers", value=str(profile.followers), inline=True)
            embed.add_field(name="Following", value=str(profile.followees), inline=True)
            embed.add_field(name="Posts", value=str(profile.mediacount), inline=True)
            await reply_function(embed=embed)
        except instaloader.exceptions.InstaloaderException:
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
        except instaloader.exceptions.InstaloaderException:
            embed = discord.Embed(
                    title="Sorry! There is some problem.",
                    description="Possibly the user is private or the post doesn't exist.",
                    color=0xBEBEFE,
                    )
            await reply_function(embed=embed)

    async def send_reel(self, reply_function, url):
        # send a reel
        try:
            #Find the post from the url
            shortcode = url.split("/")[-2]  # (https://www.instagram.com/reel/<shortcode>/<post_id>)
            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
            # Download the post
            self.loader.download_post(post, target=temp_download_dir)
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