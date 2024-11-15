#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Maintains a watchlist of movies and shows for the server '''

#-------------------------------------------------------------------------------

import os
import yaml
import asyncio
import typing
import discord
import requests
from discord.ext import commands
from discord.ext.commands import Context


class Watchlist(commands.Cog, name='Watchlist'):
    def __init__(self, bot):
        self.bot = bot
        self.watchlist = dict()
        self.announcement_config = dict()
        self.load_watchlist()
        self.api_key = '99fff185'  # OMDb API key (free) -# Hide this key later

    @commands.command(name='watchlist', description="Show the watchlist", aliases=['list', 'wl'])
    async def show_watchlist(self, context: Context):
        ''' Show the watchlist '''
        if str(context.guild.id) not in self.watchlist.keys() or not self.watchlist[str(context.guild.id)]:
            embed = discord.Embed(
                title="Watchlist is empty :confused:",
                description="Add some movies or shows to the watchlist first.",
                color=self.bot.default_color
            )
            await context.send(embed=embed)
            self.bot.log.info(f"Watchlist is empty in guild {context.guild.name}", context.guild)
            return
        n_movies = len(self.watchlist[str(context.guild.id)])    
        if n_movies < 25:
            embed = discord.Embed(
                title="Watchlist",
                description=f"Total movies/shows: {n_movies}",
                color=self.bot.default_color
            )
            for idx, entry in enumerate(self.watchlist[str(context.guild.id)]):
                embed.add_field(name=f"{idx + 1}. {entry['name']}", value=f"Suggested by: <@{entry['suggested_by']}>", inline=False)
                await context.send(embed=embed)
        else:
            for page in range(0, n_movies, 25):
                embed = discord.Embed(
                    title="Watchlist",
                    description=f"Total movies/shows: {n_movies} | (Page {page//25 + 1} of {n_movies//25 + 1})",
                    color=self.bot.default_color
                )
                for idx, entry in enumerate(self.watchlist[str(context.guild.id)][page:page+25]):
                    embed.add_field(name=f"{page + idx + 1}. {entry['name']}", value=f"Suggested by: <@{entry['suggested_by']}>", inline=False)
                await context.send(embed=embed)
        self.bot.log.info(f"Watchlist shown in guild {context.guild.name}", context.guild)
    
    @commands.command(name='add_to_watchlist', description="Add a movie or show to the watchlist", aliases=['add', 'aw'])
    async def add_to_watchlist(self, context: Context, *title_or_link: str):
        ''' Add a movie or show to the watchlist'''
        link = ' '.join(title_or_link)
        if link.startswith('https://www.imdb.com/title/') :
            imdb_id = link.split('/')[4]
            selected_item = self.get_movie_details(imdb_id)
            if selected_item is None:
                embed = discord.Embed(
                    title="Sorry :confused:",
                    description="I couldn't find any movie or show with that IMDb link.",
                    color=self.bot.default_color
                )
                await context.send(embed=embed)
                return
        else:
            if len(title_or_link) > 1 and title_or_link[-1].isdigit() and len(title_or_link[-1]) == 4:
                year = title_or_link[-1]
                title = ' '.join(title_or_link[:-1])
            else:
                year = None
                title = ' '.join(title_or_link)
            search_results = self.search_movie(title, year)
            if not search_results:
                embed = discord.Embed(
                    title="Sorry :confused:",
                    description="I couldn't find any movie or show with that title.",
                    color=self.bot.default_color
                )
                await context.send(embed=embed)
                return
            selected_item = await self.prompt_user_to_select(context, search_results)
            if selected_item is None: return
        entry = {'name': f"{selected_item['Title']} ({selected_item['Year']})",
                 'imdb_id': selected_item['imdbID'],
                 'poster': selected_item['Poster'],
                 'suggested_by': context.author.id}
        if str(context.guild.id) not in self.watchlist.keys():
            self.watchlist[str(context.guild.id)] = list()
        self.watchlist[str(context.guild.id)].append(entry)
        self.save_watchlist()
        self.bot.log.info(f"Added {entry['name']} to the watchlist in guild {context.guild.name} by {context.author.name}", context.guild)
        await self.show_detailed_info(context, selected_item['imdbID'], f"Added {entry['name']} to the watchlist :white_check_mark:")
    
    @commands.command(name='announce', description="Announce a movie or show streaming in the server", aliases=['an'])
    async def announce_movie(self, context: Context, index: int):
        ''' Announce a movie or show streaming in the server '''
        if str(context.guild.id) not in self.watchlist.keys() or not self.watchlist[str(context.guild.id)]:
            embed = discord.Embed(
                title="Watchlist is empty :confused:",
                description="Add some movies or shows to the watchlist first.",
                color=self.bot.default_color
            )
            await context.send(embed=embed)
            self.bot.log.info(f"Watchlist is empty in guild {context.guild.name}", context.guild)
            return
        if 1 <= index <= len(self.watchlist[str(context.guild.id)]):
            entry = self.watchlist[str(context.guild.id)][index - 1]
            channel = context.channel
            role = None
            if str(context.guild.id) in self.announcement_config.keys():
                if 'channel' in self.announcement_config[str(context.guild.id)]:
                    channel = context.guild.get_channel(self.announcement_config[str(context.guild.id)]['channel'])
                    if channel is None:
                        embed = discord.Embed(
                            title="Missing announcement channel :confused:",
                            description="Please set again the announcement channel using the `set_announcement` command.",
                            color=self.bot.default_color
                        )
                        await context.send(embed=embed)
                        self.bot.log.info(f"Invalid announcement channel in guild {context.guild.name}", context.guild)
                        return
                if 'role' in self.announcement_config[str(context.guild.id)]:
                    role = context.guild.get_role(self.announcement_config[str(context.guild.id)]['role'])
                    if role is None:
                        embed = discord.Embed(
                            title="Missing role :confused:",
                            description="Please set again the role to ping using the `set_announcement` command.",
                            color=self.bot.default_color
                        )
                        await context.send(embed=embed)
                        self.bot.log.info(f"Invalid role in guild {context.guild.name}", context.guild)
                        return
            if role is not None:
                message = f"{role.mention}\n{entry['name']} is starting in {context.guild.name} in few minutes! :popcorn:"
            else:
                message = f"{entry['name']} is starting in {context.guild.name} in few minutes! :popcorn:"
            detailed_info = self.get_movie_details(entry['imdb_id'])
            if detailed_info is None:
                embed = discord.Embed(
                    title="Failed to retrieve detailed information :confused:",
                    description="Please try again.",
                    color=self.bot.default_color
                )
                await context.send(embed=embed)
                return
            embed = self.embed_movie_details(detailed_info)
            await channel.send(message, embed=embed)
            self.bot.log.info(f"Announced {entry['name']} in guild {context.guild.name}", context.guild)
    
    @commands.command(name='checked', description="Remove a movie or show from the watchlist", aliases=['check', 'remove'])
    async def remove_from_watchlist(self, context: Context, index: int):
        ''' Remove a movie or show from the watchlist '''
        if str(context.guild.id) not in self.watchlist.keys() or not self.watchlist[str(context.guild.id)]:
            embed = discord.Embed(
                title="Watchlist is empty :confused:",
                description="Add some movies or shows to the watchlist first.",
                color=self.bot.default_color
            )
            await context.send(embed=embed)
            return
        if 1 <= index <= len(self.watchlist[str(context.guild.id)]):
            entry = self.watchlist[str(context.guild.id)].pop(index - 1)
            self.save_watchlist()
            self.bot.log.info(f"Removed {entry['name']} from the watchlist in guild {context.guild.name} by {context.author.name}", context.guild)
            await self.show_detailed_info(context, entry['imdb_id'], f"Removed {entry['name']} from the watchlist :white_check_mark:")
        else:
            embed = discord.Embed(
                title="Invalid index :confused:",
                description="Please enter a valid index.",
                color=self.bot.default_color
            )
            await context.send(embed=embed)

    @commands.command(name='search_movie', description="Search for a movie or show", aliases=['search','sm'])
    async def search_key(self, context: Context, *title: str):
        ''' Search for a movie or show '''
        if len(title) > 1 and title[-1].isdigit() and len(title[-1]) == 4:
            year = title[-1]
            title = title[:-1]
        else:
            year = None
            title = ' '.join(title)
        search_results = self.search_movie(title, year)
        if not search_results:
            embed = discord.Embed(
                title="Sorry :confused:",
                description="I couldn't find any movie or show with that title.",
                color=self.bot.default_color
            )
            await context.send(embed=embed)
            return
        selected_item = await self.prompt_user_to_select(context, search_results)
        if selected_item is None: return
        await self.show_detailed_info(context, selected_item['imdbID'], f"Search results for {title}")

    @commands.command(name='show_details', description="Show detailed information about a movie or show", aliases=['show'])
    async def show_details(self, context: Context, index: int):
        ''' Show detailed information about a movie or show '''
        if str(context.guild.id) not in self.watchlist.keys() or not self.watchlist[str(context.guild.id)]:
            embed = discord.Embed(
                title="Watchlist is empty :confused:",
                description="Add some movies or shows to the watchlist first.",
                color=self.bot.default_color
            )
            await context.send(embed=embed)
            return
        if 1 <= index <= len(self.watchlist[str(context.guild.id)]):
            entry = self.watchlist[str(context.guild.id)][index - 1]
            await self.show_detailed_info(context, entry['imdb_id'], f"Details of {entry['name']}")
        else:
            embed = discord.Embed(
                title="Invalid index :confused:",
                description="Please enter a valid index.",
                color=self.bot.default_color
            )
            await context.send(embed=embed)
    
    @commands.command(name='clear_watchlist', description="Clear the watchlist", aliases=['clear', 'cw'])
    async def clear_watchlist(self, context: Context):
        ''' Clear the watchlist '''
        self.delete_watchlist(str(context.guild.id))
        self.save_watchlist()
        embed = discord.Embed(
            title="Watchlist cleared :white_check_mark:",
            description="The watchlist is now empty.",
            color=self.bot.default_color
        )
        await context.send(embed=embed)
        self.bot.log.info(f"Watchlist cleared in guild {context.guild.name} by {context.author.name}", context.guild)

    @commands.command(name='set_announcement', description="Set the channel to announce movies and shows or the role to ping")
    async def set_announcement_channel(self, context: Context, channel: discord.TextChannel = None, role: discord.Role = None):
        ''' Set the channel to announce movies or shows '''
        if str(context.guild.id) not in self.announcement_config.keys():
            self.announcement_config[str(context.guild.id)] = dict()
        if channel is None and role is None:
            self.announcement_config.pop(str(context.guild.id), None)
            embed = discord.Embed(
                title="Announcement settings cleared :white_check_mark:",
                description="default settings for announcement are cleared",
                color=self.bot.default_color
            )
            await context.send(embed=embed)
            self.bot.log.info(f"Announcement settings cleared for guild {context.guild.name}", context.guild)
            return
        channel = context.guild.get_channel(channel.id)
        if channel is not None:
            self.announcement_config[str(context.guild.id)]['channel'] = channel.id     
        else:
            embed = discord.Embed(
                title="Invalid channel :confused:",
                description="Please enter a valid channel.",
                color=self.bot.default_color
            )
            await context.send(embed=embed)
            self.bot.log.info(f"Invalid channel in guild {context.guild.name}", context.guild)
            return
        message = f"Movie/show announcements will be made in {channel.mention}"
        if role is not None:
            role = context.guild.get_role(role.id)
            if role is not None:
                self.announcement_config[str(context.guild.id)]['role'] = role.id
                message += f" and {role.mention} will be pinged."
            else:
                embed = discord.Embed(
                    title="Invalid role :confused:",
                    description="Please enter a valid role.",
                    color=self.bot.default_color
                )
                await context.send(embed=embed)
                self.bot.log.info(f"Invalid role in guild {context.guild.name}", context.guild)
                return
        self.save_watchlist()
        embed = discord.Embed(
            title="Announcement setting set :white_check_mark:",
            description=message,
            color=self.bot.default_color
        )
        await context.send(embed=embed)
        self.bot.log.info(f"Announcement settings setting set for guild {context.guild.name}", context.guild)

    async def show_detailed_info(self, context: Context, imdbID, embed_title=None):
        detailed_info = self.get_movie_details(imdbID)
        if detailed_info is None:
            embed = discord.Embed(
                title="Failed to retrieve detailed information :confused:",
                description="Please try again.",
                color=self.bot.default_color
            )
            await context.send(embed=embed)
            self.bot.log.info(f"Failed to retrieve detailed information for {imdbID} in guild {context.guild.name}", context.guild)
            return
        embed = self.embed_movie_details(detailed_info, embed_title)
        await context.send(embed=embed)

    def embed_movie_details(self, detailed_info, embed_title=None):
        embed = discord.Embed()
        if embed_title:
            embed.title = embed_title
        else:
            embed.title = f"{detailed_info['Title']} ({detailed_info['Year']})"
        embed.add_field(name="Genre", value=detailed_info['Genre'], inline=True)
        embed.add_field(name="Released", value=detailed_info['Released'], inline=True)
        embed.add_field(name="Runtime", value=detailed_info['Runtime'], inline=True)
        embed.add_field(name="Plot", value=detailed_info['Plot'], inline=False)
        embed.add_field(name="Director", value=detailed_info['Director'], inline=True)
        embed.add_field(name="Actors", value=detailed_info['Actors'], inline=True)
        embed.add_field(name="Language", value=detailed_info['Language'], inline=True)
        embed.add_field(name="Country", value=detailed_info['Country'], inline=True)
        if detailed_info.get('Poster').startswith('http'):
            embed.set_image(url=detailed_info['Poster'])
        embed.color = self.bot.default_color
        return embed

    async def prompt_user_to_select(self, context: Context, search_results):
        embeds = []
        n_results_found = len(search_results)
        if n_results_found < 8:
            embed = discord.Embed(
                title="Please select the movie you want to add to the watchlist",
                description=f"Enter the number of the movie you want to add [1-{n_results_found}], or enter `0` to cancel (30 seconds)",
                color=self.bot.default_color
            )
            embeds.append(embed)
        else:
            embed = discord.Embed(
                title="Please select the movie you want to add to the watchlist",
                description=f"Enter the number of the movie you want to add [1-8], or enter `0` to cancel (30 seconds) or type '9' to see more results",
                color=self.bot.default_color
            )
            embeds.append(embed)
        for idx, movie in enumerate(search_results[:8]):
            embed = discord.Embed(
                title=f"{idx + 1}. {movie['Title']}",
                description=f"Year: {movie['Year']}\nType: {movie['Type']}\nIMDb ID: {movie['imdbID']}",
                color=self.bot.default_color
            )
            if movie.get('Poster').startswith('http'):
                embed.set_thumbnail(url=movie['Poster'])
            embeds.append(embed)
        await context.send(embeds=embeds)
        def check(m):
            return m.author == context.author and m.channel == context.channel and m.content.isdigit() and 0 <= int(m.content) <= 9
        try:
            user_response = await self.bot.wait_for('message', check=check, timeout=30.0)
            selected_item = search_results[int(user_response.content) - 1]
            if int(user_response.content) == 0:
                await context.send("Cancelled")
            elif int(user_response.content) == 9:
                return await self.prompt_user_to_select(context, search_results[8:])
            else:
                return selected_item
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="You took too long to respond :timer:",
                description="Please try again.",
                color=self.bot.default_color
            )
            await context.send(embed=embed)
            return None
        
    def search_movie(self, title, year=None):
        if year:
            url = f'http://www.omdbapi.com/?s={title}&y={year}&apikey={self.api_key}'
        else:
            url = f'http://www.omdbapi.com/?s={title}&apikey={self.api_key}'
        response = requests.get(url).json()
        if response.get('Response') == 'True':
            return response.get('Search')
        return None
    
    def get_movie_details(self, imdb_id):
        url = f'http://www.omdbapi.com/?i={imdb_id}&apikey={self.api_key}'
        response = requests.get(url).json()
        if response.get('Response') == 'True':
            return response
        return None
        
    def save_watchlist(self):
        # Save the watchlist to a file
        if os.path.exists(self.bot.data_dir):
            guilds = os.listdir(self.bot.data_dir)
            for guild_id in guilds:
                if guild_id in self.watchlist.keys():
                    with open(os.path.join(self.bot.data_dir, guild_id, 'watchlist.yaml'), 'w+') as file:
                        yaml.dump(self.watchlist[guild_id], file)
                if guild_id in self.announcement_config.keys():
                    with open(os.path.join(self.bot.data_dir, guild_id, 'announcement_config.yaml'), 'w+') as file:
                        yaml.dump(self.announcement_config[guild_id], file)
                    self.bot.log.info(f"Saved watchlist for guild {guild_id}")
    
    def load_watchlist(self):
        # Load the watchlist from a file
        if os.path.exists(self.bot.data_dir):
            guilds = os.listdir(self.bot.data_dir)
            for guild_id in guilds:
                if os.path.exists(os.path.join(self.bot.data_dir, guild_id, 'watchlist.yaml')):
                    with open(os.path.join(self.bot.data_dir, guild_id, 'watchlist.yaml'), 'r') as file:
                        watchlist = yaml.load(file, Loader=yaml.FullLoader)
                        if watchlist is not None:
                            if guild_id not in self.watchlist:
                                self.watchlist[guild_id] = list()
                            self.watchlist[guild_id] = watchlist
                            self.bot.log.info(f"Loaded watchlist for guild {guild_id}")
                else:
                    self.bot.log.info(f"No watchlist found for guild {guild_id}")
                if os.path.exists(os.path.join(self.bot.data_dir, guild_id, 'announcement_config.yaml')):
                    with open(os.path.join(self.bot.data_dir, guild_id, 'announcement_config.yaml'), 'r') as file:
                        announcement_config = yaml.load(file, Loader=yaml.FullLoader)
                        if announcement_config is not None:
                            if guild_id not in self.announcement_config:
                                self.announcement_config[guild_id] = dict()
                            self.announcement_config[guild_id] = announcement_config
                            self.bot.log.info(f"Loaded announcement config for guild {guild_id}")
    
    def delete_watchlist(self, guild_id):
        # Delete the watchlist for a guild
        if os.path.exists(os.path.join(self.bot.data_dir, guild_id)):
            os.remove(os.path.join(self.bot.data_dir, guild_id, 'watchlist.yaml'))
            self.bot.log.info(f"Deleted watchlist for guild {guild_id}")
        self.watchlist.pop(guild_id, None)


async def setup(bot):
    await bot.add_cog(Watchlist(bot))