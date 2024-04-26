#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Command related to search and its related functions'''

#-------------------------------------------------------------------------------

import os
import re
import yaml
import asyncio
import discord
from discord.ext import commands
from discord.ext.commands import Context
from googlesearch import search
try:
    from bs4 import BeautifulSoup
except ImportError:
    os.system("pip install beautifulsoup4")
    from bs4 import BeautifulSoup
import requests

class Search(commands.Cog, name="Search"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command( name="keyword_search", description="Google search with keyword")
    async def search(self, context: Context, *, keyword: str):
        ''' Google search with keyword '''
        search_results = search(keyword, advanced=True, num_results=1)
        for result in search_results:
            embed = discord.Embed(
                title=result.title,
                description=result.description,
                url = result.url,
                color=self.bot.default_color,
            )
            await context.send(embed=embed)

    @commands.command( name="person_search", description="Google search with person name")
    async def person_search(self, context: Context, *, person_name: str):
        ''' Google search with person name '''
        search_results = search(person_name, advanced=True, num_results=1)
        for result in search_results:
            embed = discord.Embed(
                title=result.title,
                description=result.description,
                url = result.url,
                color=self.bot.default_color,
            )
            await context.send(embed=embed)

    @commands.command( name="general_knowledge", description="General knowledge search")
    async def general_knowledge(self, context: Context, *, keyword: str):
        ''' General knowledge search '''
        search_results = search(keyword, advanced=True, num_results=1)
        for result in search_results:
            embed = discord.Embed(
                title=result.title,
                description=result.description,
                url = result.url,
                color=self.bot.default_color,
            )
            await context.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Search(bot))

