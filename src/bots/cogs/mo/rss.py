#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Command related to RSS feed '''

#-------------------------------------------------------------------------------

import os
import re
import yaml
import asyncio
import typing
import discord
from discord.ext import tasks
from discord.ext import commands
from discord.ext.commands import Context
from collections import defaultdict
try:
    import feedparser
except ImportError:
    #install feedparser
    os.system("pip install feedparser")
try:
    import googlesearch
except ImportError:
    #install googlesearch
    os.system("pip install googlesearch-python")

class RSSFeed(commands.Cog, name="RSS Feed"):
    def __init__(self, bot):
        self.bot = bot
        self.subscribed_feeds = dict()
        self.load_subscribed_feeds()

        self.feed_states = defaultdict(dict)
        self.fetch_updates.start()

    @commands.command( name="rss_feed", description="Get RSS feed")
    async def rss_feed(self, context: Context, feed_url: str):
        ''' Get RSS feed '''
        feed = feedparser.parse(feed_url)
        if feed is not None:
            embed = discord.Embed(
                title=feed.feed.title,
                description=feed.feed.description,
                color=self.bot.default_color,
                url=feed.feed.link,
            )
            for entry in feed.entries[:5]:
                embed.add_field(
                    name=entry.title,
                    value=entry.summary,
                    inline=False
                )
            await context.send(embed=embed)
        else:
            embed = discord.Embed(
                title="RSS Feed",
                description="Invalid RSS feed",
                color=self.bot.default_color,
            )
            await context.send(embed=embed)

    @tasks.loop(minutes=15)  # Check feeds every 15 minutes
    async def fetch_updates(self):
        for guild_id, channels in self.subscribed_feeds.items():
            for channel_id, feeds in channels.items():
                channel = self.bot.get_channel(int(channel_id))
                if channel:
                    for feed_url in feeds:
                        try:
                            feed = feedparser.parse(feed_url)
                            if feed.entries:
                                last_sent_entry = self.feed_states[guild_id].get(feed_url)
                                new_entries = []
                                for entry in feed.entries:
                                    if last_sent_entry is None or entry.id != last_sent_entry:
                                        new_entries.append(entry)
                                if new_entries:
                                    for entry in new_entries[:5]:
                                        embed = discord.Embed(
                                            title=entry.title,
                                            description=entry.summary,
                                            color=self.bot.default_color,
                                            url=entry.link
                                        )
                                        await channel.send(embed=embed)
                                    # Update state with the ID of the latest entry
                                    self.feed_states[guild_id][feed_url] = new_entries[0].id
                        except Exception as e:
                            self.bot.log.error(f"Error fetching RSS feed {feed_url}: {e}", channel.guild)

    @fetch_updates.before_loop
    async def before_fetch_updates(self):
        await self.bot.wait_until_ready()



    @commands.command( name="rss_subscribe", description="Subscribe to an RSS feed")
    async def rss_subscribe(self, context: Context, feed_url: str, channel: typing.Optional[discord.TextChannel] = None):
        ''' Subscribe to given RSS feed '''
        if channel is None:
            channel = context.channel
        if str(context.guild.id) not in self.subscribed_feeds.keys():
            self.subscribed_feeds[str(context.guild.id)] = dict()
        if str(channel.id) not in self.subscribed_feeds[str(context.guild.id)].keys():
            self.subscribed_feeds[str(context.guild.id)][str(channel.id)] = list()
        if feed_url not in self.subscribed_feeds[str(context.guild.id)][str(channel.id)]: 
            self.subscribed_feeds[str(context.guild.id)][str(channel.id)].append(feed_url)
            self.save_subscribed_feeds()
            embed = discord.Embed(
                title="RSS Feed Subscription",
                description=f"Subscribed to {feed_url}",
                color=self.bot.default_color,
            )
            await context.send(embed=embed)
            self.bot.log.info("Subscribed to RSS feed " + feed_url + " in channel " + str(channel.id), context.guild)
        else:
            embed = discord.Embed(
                title="RSS Feed Subscription",
                description=f"Already subscribed to {feed_url}",
                color=self.bot.default_color,
            )
            await context.send(embed=embed)
            self.bot.log.info("Already subscribed to RSS feed " + feed_url + " in channel " + str(channel.id), context.guild)
    
    @commands.command( name="rss_unsubscribe", description="Unsubscribe from an RSS feed")
    async def rss_unsubscribe(self, context: Context, feed_url: str, channel: typing.Optional[discord.TextChannel] = None):
        ''' Unsubscribe from given RSS feed '''
        if channel is None:
            channel = context.channel
        if str(context.guild.id) not in self.subscribed_feeds.keys():
            self.subscribed_feeds[str(context.guild.id)] = dict()
        if str(channel.id) not in self.subscribed_feeds[str(context.guild.id)].keys():
            self.subscribed_feeds[str(context.guild.id)][str(channel.id)] = list()
        if feed_url in self.subscribed_feeds[str(context.guild.id)][str(channel.id)]: 
            self.subscribed_feeds[str(context.guild.id)][str(channel.id)].remove(feed_url)
            if len(self.subscribed_feeds[str(context.guild.id)][str(channel.id)]) == 0:
                del self.subscribed_feeds[str(context.guild.id)][str(channel.id)]
            self.save_subscribed_feeds()
            embed = discord.Embed(
                title="RSS Feed Subscription",
                description=f"Unsubscribed from {feed_url}",
                color=self.bot.default_color,
            )
            await context.send(embed=embed)
            self.bot.log.info("Unsubscribed from RSS feed " + feed_url + " in channel " + str(channel.id), context.guild)
        else:
            embed = discord.Embed(
                title="RSS Feed Subscription",
                description=f"Not subscribed to {feed_url}",
                color=self.bot.default_color,
            )
            await context.send(embed=embed)
            self.bot.log.info("Not subscribed to RSS feed " + feed_url + " in channel " + str(channel.id), context.guild)
    
    @commands.command( name="feed_list", description="List all subscribed RSS feeds")
    async def feed_list(self, context: Context):
        ''' List all subscribed RSS feeds '''
        if str(context.guild.id) in self.subscribed_feeds.keys():
            embed = discord.Embed(
                title="RSS Feed Subscription",
                description="List of all subscribed RSS feeds",
                color=self.bot.default_color,
            )
            for channel_id in self.subscribed_feeds[str(context.guild.id)].keys():
                channel = context.guild.get_channel(int(channel_id))
                if channel is not None:
                    embed.add_field(
                        name=f"Channel: {channel.name}",
                        value="\n".join(self.subscribed_feeds[str(context.guild.id)][channel_id]),
                        inline=False
                    )
            await context.send(embed=embed)
        else:
            embed = discord.Embed(
                title="RSS Feed Subscription",
                description="No RSS feeds subscribed",
                color=self.bot.default_color,
            )
            await context.send(embed=embed)

    def load_subscribed_feeds(self):
        # load subscribed rss feeds of all guilds
        if os.path.exists(self.bot.data_dir):
            guilds = os.listdir(self.bot.data_dir)
            for guild_id in guilds:
                if os.path.exists(os.path.join(self.bot.data_dir, guild_id, "rss_subscription.yml")):
                    with open(os.path.join(self.bot.data_dir, guild_id, "rss_subscription.yml"), 'r') as file:
                        subsribed_feeds = yaml.safe_load(file)
                        if subsribed_feeds is not None:
                            if guild_id not in self.subscribed_feeds:
                                self.subscribed_feeds[guild_id] = dict()
                            for channel_id in subsribed_feeds.keys():
                                self.subscribed_feeds[guild_id][channel_id] = subsribed_feeds[channel_id]
                    self.bot.log.info(f"RSS feeds loaded for guild {guild_id}")
                else:
                    self.bot.log.info(f"No RSS feeds found for guild {guild_id}")
    
    def save_subscribed_feeds(self):
        # save subscribed rss feeds of all guilds
        if os.path.exists(self.bot.data_dir):
            guilds = os.listdir(self.bot.data_dir)
            for guild_id in guilds:
                if guild_id in self.subscribed_feeds.keys():
                    with open(os.path.join(self.bot.data_dir, guild_id, "rss_subscription.yml"), 'w') as file:
                        yaml.dump(self.subscribed_feeds[guild_id], file)
                    self.bot.log.info(f"RSS feeds saved for guild {guild_id}")


async def setup(bot):
    await bot.add_cog(RSSFeed(bot))