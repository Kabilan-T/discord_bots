#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Command related to search and related API'''

#-------------------------------------------------------------------------------

import os
import re
import yaml
import asyncio
import discord
import urllib.parse
import googlesearch
from discord.ext import commands
from discord.ext.commands import Context


class Search(commands.Cog, name="Search"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="search", aliases=["s"])
    async def search(self, ctx: Context, *, query: str):
        '''Search for a query in the search engine'''

        query = urllib.parse.quote(query)
        search_url = f"https://www.google.com/search?q={query}"
        await ctx.send(search_url)
    
    @commands.command(name="google", aliases=["g"])
    async def google(self, ctx: Context, *, query: str):
        '''Search for a query in google'''
        try:
            search_result = googlesearch.search(query)
            await ctx.send("\n".join(search_result))
        except Exception as e:
            await ctx.send(f"Error: {e}")


    @commands.command(name="wiki", aliases=["w"])
    async def wiki(self, ctx: Context, *, query: str):
        '''Search for a query in wikipedia'''

        query = urllib.parse.quote(query)
        search_url = f"https://en.wikipedia.org/wiki/{query}"
        await ctx.send(search_url)

    @commands.command(name="urban", aliases=["u"])
    async def urban(self, ctx: Context, *, query: str):
        '''Search for a query in urban dictionary'''

        query = urllib.parse.quote(query)
        search_url = f"https://www.urbandictionary.com/define.php?term={query}"
        await ctx.send(search_url)

    @commands.command(name="youtube", aliases=["yt"])
    async def youtube(self, ctx: Context, *, query: str):
        '''Search for a query in youtube'''

        query = urllib.parse.quote(query)
        search_url = f"https://www.youtube.com/results?search_query={query}"
        await ctx.send(search_url)


async def setup(bot):
    await bot.add_cog(Search(bot))