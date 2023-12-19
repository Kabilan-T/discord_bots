#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Command related to instagram and its API'''

#-------------------------------------------------------------------------------

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
        profile = instaloader.Profile.from_username(self.loader.context, username)
        if profile.is_private:
            embed = discord.Embed(
                title=str(profile.full_name),
                description="This profile is private.",
                color=0xBEBEFE,
            )
        else:
            embed = discord.Embed(
                title=str(profile.full_name),
                description=profile.biography,
                color=0xBEBEFE,
            )
        await context.send(embed=embed)

    @commands.hybrid_command( name="show", description="Download a post from instagram.")
    async def show_post(self, context: Context, url: str):
        # Embed a post from instagram
        if len(url.split("/")) != 6:  # Check if the url is valid for a post (https://www.instagram.com/p/<shortcode>/<post_id>)
            await context.send("Invalid URL. Doesn't seems to be a post.")
            return
        shortcode = url.split("/")[-2]
        post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
        embed = discord.Embed(
            title=str(post.owner_profile.full_name),
            description="Profile: https://www.instagram.com/"+str(post.owner_profile.username)+"\nCaption: "+str(post.caption)+"\nLikes: "+str(post.likes)+"\n",
            color=0xBEBEFE,
        )
        embed.set_image(url=post.url)
        await context.send(embed=embed)

    @commands.hybrid_command( name="set_channel", description="Set the channel to watch for instagram links.")
    async def set_channel(self, context: Context, channel: discord.TextChannel):
        # Set the channel to watch for instagram links
        self.channel_to_watch = channel
        await context.send("Instagram channel set to "+channel.mention+".")
    
    #check the channel for instagram links if it is set to watch if so download the post
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel == self.channel_to_watch:
            if str("https://www.instagram.com/") in message.content:
                if len(message.content.split("/")) == 6: # Check if the url is valid for a post (https://www.instagram.com/p/<shortcode>/<post_id>)
                    shortcode = message.content.split("/")[-2]
                    post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
                    embed = discord.Embed(
                        title=str(post.owner_profile.full_name),
                        description="Profile: https://www.instagram.com/"+str(post.owner_profile.username)+"\nCaption: "+str(post.caption)+"\nLikes: "+str(post.likes)+"\n",
                        color=0xBEBEFE,
                    )
                    embed.set_image(url=post.url)
                    await message.reply(embed=embed)


                
async def setup(bot):
    await bot.add_cog(Instagram(bot))