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

    @commands.command(name='search', aliases=['sm'], description="Search for a movie or show")
    async def search_key(self, context: Context, *title: str):
        ''' Search for a movie or show '''
        title = ' '.join(title)
        search_results = self.search_movie(title)
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

    @commands.command(name='add_to_watchlist', aliases=['add', 'a'], description="Add a movie or show to the watchlist")
    async def add_to_watchlist(self, context: Context, *title: str):
        ''' Add a movie or show to the watchlist'''
        # if title is a imdb link
        title = ' '.join(title)
        if title.startswith('https://www.imdb.com/title/'):
            imdb_id = title.split('/')[4]
            detailed_info = self.get_movie_details(imdb_id)
            if detailed_info is None:
                embed = discord.Embed(
                    title="Failed to retrieve detailed information :confused:",
                    description="Please try again.",
                    color=self.bot.default_color
                )
                await context.send(embed=embed)
                return
            selected_item = {'Title': detailed_info['Title'], 'Year': detailed_info['Year'], 'imdbID': imdb_id, 'Poster': detailed_info['Poster']}
        else:
            search_results = self.search_movie(title)
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
        await self.show_detailed_info(context, selected_item['imdbID'], f"Added {entry['name']} to the watchlist :white_check_mark:")
    
    @commands.command(name='checked', aliases=['c', 'remove', 'check'], description="Remove a movie or show from the watchlist")
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
            await self.show_detailed_info(context, entry['imdb_id'], f"Removed {entry['name']} from the watchlist :white_check_mark:")
        else:
            embed = discord.Embed(
                title="Invalid index :confused:",
                description="Please enter a valid index.",
                color=self.bot.default_color
            )
            await context.send(embed=embed)
    
    @commands.command(name='show_details', aliases=['show', 'details', 'sd'], description="Show detailed information about a movie or show")
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

    @commands.command(name='watchlist', aliases=['wl', 'list'], description="Show the watchlist")
    async def show_watchlist(self, context: Context):
        ''' Show the watchlist '''
        if str(context.guild.id) not in self.watchlist.keys() or not self.watchlist[str(context.guild.id)]:
            embed = discord.Embed(
                title="Watchlist is empty :confused:",
                description="Add some movies or shows to the watchlist first.",
                color=self.bot.default_color
            )
            await context.send(embed=embed)
            return
        n_movies = len(self.watchlist[str(context.guild.id)])
        embed = discord.Embed(
                title="Watchlist",
                description=f"Total movies/shows: {n_movies}",
                color=self.bot.default_color
            )
        for idx, entry in enumerate(self.watchlist[str(context.guild.id)]):
            embed.add_field(name=f"{idx + 1}. {entry['name']}", value=f"Suggested by: <@{entry['suggested_by']}>", inline=False)
        await context.send(embed=embed)
    
    @commands.command(name='clear_watchlist', aliases=['clear', 'cw'], description="Clear the watchlist")
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

    
    @commands.command(name='set_announcement', aliases=['sa'], description="Set the channel to announce movies or shows and the role to ping")
    async def set_announcement_channel(self, context: Context, channel: discord.TextChannel = None, role: discord.Role = None):
        ''' Set the channel to announce movies or shows '''
        if channel is None:
            channel = context.channel
        if str(context.guild.id) not in self.announcement_config.keys():
            self.announcement_config[str(context.guild.id)] = dict()
        self.announcement_config[str(context.guild.id)]['channel'] = channel.id
        if role is not None:
            self.announcement_config[str(context.guild.id)]['role'] = role.id
        self.save_watchlist()
        embed = discord.Embed(
            title="Announcement channel set :white_check_mark:",
            description=f"Movies or shows will be announced in {channel.mention}",
            color=self.bot.default_color
        )
        await context.send(embed=embed)

    @commands.command(name='announce', aliases=['an'], description="Announce a movie or show streaming in the server")
    async def announce_movie(self, context: Context, index: int, time: typing.Optional[str] = None):
        ''' Announce a movie or show streaming in the server '''
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
            if str(context.guild.id) not in self.announcement_config.keys() or 'channel' not in self.announcement_config[str(context.guild.id)]:
                embed = discord.Embed(
                    title="Announcement channel not set :confused:",
                    description="Please set the announcement channel first.",
                    color=self.bot.default_color
                )
                await context.send(embed=embed)
                return
            channel = context.guild.get_channel(self.announcement_config[str(context.guild.id)]['channel'])
            if channel is None:
                embed = discord.Embed(
                    title="Invalid announcement channel :confused:",
                    description="Please set the announcement channel again.",
                    color=self.bot.default_color
                )
                await context.send(embed=embed)
                return
            if 'role' in self.announcement_config[str(context.guild.id)]:
                role = context.guild.get_role(self.announcement_config[str(context.guild.id)]['role'])
                if role is None:
                    embed = discord.Embed(
                        title="Invalid role :confused:",
                        description="Please set the role to ping again.",
                        color=self.bot.default_color
                    )
                    await context.send(embed=embed)
                    return
                if time:
                    message = f"{role.mention}\n{entry['name']} is starting in {time} minutes in {context.guild.name}! :popcorn:"
                else:
                    message = f"{role.mention}\n{entry['name']} is starting in {context.guild.name} in few minutes! :popcorn:"
            else:
                if time:
                    message = f"{entry['name']} is starting in {time} minutes in {context.guild.name}! :popcorn:"
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

    async def show_detailed_info(self, context: Context, imdbID, embed_title=None):
        detailed_info = self.get_movie_details(imdbID)
        if detailed_info is None:
            embed = discord.Embed(
                title="Failed to retrieve detailed information :confused:",
                description="Please try again.",
                color=self.bot.default_color
            )
            await context.send(embed=embed)
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