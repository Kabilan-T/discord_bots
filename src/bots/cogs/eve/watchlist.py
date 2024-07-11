#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Maintains a watchlist of movies and shows for the server '''

#-------------------------------------------------------------------------------

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
        self.api_key = '99fff185'  # OMDb API key (free) -# Hide this key later

    @commands.command(name='add_to_watchlist', aliases=['add', 'a'], description="Add a movie or show to the watchlist")
    async def add_to_watchlist(self, context: Context, *title: str, year: typing.Optional[int] = None):
        ''' Add a movie or show to the watchlist'''
        title = ' '.join(title)
        if year and 1900 <= year <= 2100:
            search_results = self.search_movie(title, year)
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
        detailed_info = self.get_movie_details(selected_item['imdbID'])
        if detailed_info is None:
            embed = discord.Embed(
                title="Failed to retrieve detailed information :confused:",
                description="Please try again.",
                color=self.bot.default_color
            )
            await context.send(embed=embed)
            return
        if context.guild.id not in self.watchlist:
            self.watchlist[context.guild.id] = list()
        entry = {'name': f"{detailed_info['Title']} ({detailed_info['Year']})",
                 'details': detailed_info, 
                 'suggested_by': context.author.id}
        self.watchlist[context.guild.id].append(entry)
        embed = self.embed_watchlist_entry(entry, f"Added {entry['name']} to the watchlist :white_check_mark:")
        await context.send(embed=embed)
    
    @commands.command(name='show_watchlist', aliases=['list'], description="Show the watchlist")
    async def show_watchlist(self, context: Context):
        ''' Show the watchlist '''
        if context.guild.id not in self.watchlist or not self.watchlist[context.guild.id]:
            embed = discord.Embed(
                title="Watchlist is empty :confused:",
                description="Add some movies or shows to the watchlist first.",
                color=self.bot.default_color
            )
            await context.send(embed=embed)
            return
        embeds = []
        for idx, entry in enumerate(self.watchlist[context.guild.id], start=1):
            embed = self.embed_watchlist_entry(entry, f"Entry {idx}")
            embeds.append(embed)
        await context.send(embeds=embeds)
                
    def embed_watchlist_entry(self, entry, embed_title=None):
        detailed_info = entry['details']
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
    


             

async def setup(bot):
    await bot.add_cog(Watchlist(bot))