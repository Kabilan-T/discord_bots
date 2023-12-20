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



class Instagram(commands.Cog, name="Instagram"):
    def __init__(self, bot):
        self.bot = bot
        self.channel_to_watch = None
        self.loader = instaloader.Instaloader()
    
    @commands.hybrid_command( name="bio", description="Get the bio of a user.")
    async def bio(self, context: Context, username: str):
        # Get the bio of a user
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
            await context.send(embed=embed)
        except instaloader.exceptions.InstaloaderException:
            embed = discord.Embed(
                    title="Sorry! There is some problem.",
                    description="Possibly the username is wrong or doesn't exist.",
                    color=0xBEBEFE,
                    )
            await context.send(embed=embed)
        
    @commands.hybrid_command( name="show", description="Download a post from instagram.")
    async def show_post(self, context: Context, url: str):
        # Download a post from instagram and show it        
        try:
            #Find the post from the url
            shortcode = url.split("/")[-2]  # (https://www.instagram.com/p/<shortcode>/<post_id>)
            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
            # Download the post
            self.loader.download_post(post, target="downloads")
            media_files = [discord.File("downloads/"+file) for file in os.listdir(os.getcwd()+"/downloads") 
                            if file.endswith(".jpg") or file.endswith(".mp4") or file.endswith(".png") or file.endswith(".jpeg") or file.endswith(".gif")]
            os.system("rm -rf downloads/*")
            # Send the post with caption and likes as embed message
            short_caption = post.caption.split("\n")[0] if post.caption.split("\n")[0] else post.caption.split("\n")[0][:50]+"..."
            embed = discord.Embed(
                title=str(post.owner_profile.full_name),
                url="https://www.instagram.com/"+str(post.owner_profile.username),
                description="Caption: "+str(short_caption)+"\nLikes: "+str(post.likes)+"\n",
                color=0xBEBEFE,
            )
            embed.set_thumbnail(url=post.owner_profile.profile_pic_url)
            await context.send(embed=embed, files=media_files)
        except instaloader.exceptions.InstaloaderException:
            embed = discord.Embed(
                    title="Sorry! There is some problem.",
                    description="Possibly the user is private or the post doesn't exist.",
                    color=0xBEBEFE,
                    )
            await context.send(embed=embed)

    @commands.hybrid_command( name="set_channel", description="Set the channel to watch for instagram links.")
    async def set_channel(self, context: Context, channel: discord.TextChannel):
        # Set the channel to watch for instagram links
        self.channel_to_watch = channel
        await context.send("Instagram channel set to "+channel.mention+".")
    
    #check the channel for instagram links if it is set to watch if so download the post
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel == self.channel_to_watch and message.author.bot == False and message.content != "":
            if str("https://www.instagram.com/") in message.content:
                if len(message.content.split("/")) == 6:
                    # Link is of a post - download and send it
                    try:
                        # Find the post from the url 
                        shortcode = message.content.split("/")[-2]  # (https://www.instagram.com/p/<shortcode>/<post_id>)
                        post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
                        # Download the post
                        self.loader.download_post(post, target="downloads")
                        media_files = [discord.File("downloads/"+file) for file in os.listdir(os.getcwd()+"/downloads") 
                                        if file.endswith(".jpg") or file.endswith(".mp4") or file.endswith(".png") or file.endswith(".jpeg") or file.endswith(".gif")]
                        os.system("rm -rf downloads/*")
                        # Send the post with caption and likes as embed message
                        short_caption = post.caption.split("\n")[0] if post.caption.split("\n")[0] else post.caption.split("\n")[0][:50]+"..."
                        embed = discord.Embed(
                            title=str(post.owner_profile.full_name),
                            url="https://www.instagram.com/"+str(post.owner_profile.username),
                            description="Caption: "+str(short_caption)+"\nLikes: "+str(post.likes)+"\n",
                            color=0xBEBEFE,
                        )
                        embed.set_thumbnail(url=post.owner_profile.profile_pic_url)
                        await message.reply(embed=embed, files=media_files)
                    except instaloader.exceptions.InstaloaderException:
                        return
                elif len(message.content.split("/")) == 4:
                    # Link is of a profile - get the bio
                    try:
                        username = message.content.split("/")[-1]# (https://www.instagram.com/<username>)
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
                        await message.reply(embed=embed)
                    except instaloader.exceptions.InstaloaderException:
                        return
                else:
                    return
                
                
async def setup(bot):
    await bot.add_cog(Instagram(bot))