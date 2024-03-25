#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Cricket related commands and API calls '''

#-------------------------------------------------------------------------------

import os
import re
import yaml
import time
import discord
import requests
from discord.ext import commands
from discord.ext.commands import Context
from bs4 import BeautifulSoup

class Cricket(commands.Cog, name="Cricket"):
    def __init__(self, bot):
        '''Initializes the cricket cog'''
        self.bot = bot
        self.base_url = "https://www.cricbuzz.com/"
        self.subscribed = False
        self.subscribed_channel = None
    
    @commands.command(name="live_scores", aliases=["ls"], help="Get the live cricket scores")
    async def live_scores(self, ctx: Context):
        '''Get the live cricket scores'''
        url = self.base_url + "cricket-match/live-scores"
        time.sleep(1)
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        div = soup.find("div", 
                        attrs={"ng-show": "active_match_type == 'league-tab'"})
        matches = div.find_all(class_="cb-mtch-lst cb-col cb-col-100 cb-tms-itm")

        embed = discord.Embed(title="Live Cricket Scores", color=discord.Color.green())

        for match in matches:
            team_names = match.find("h3").text.strip().replace(",", "")
            status = match.find(
                "div", attrs={"class": "cb-text-live"}).text.strip()
            score = match.find_all(
                "div", attrs={"style": "display:inline-block; width:140px"})[0].text.strip() if match.find_all(
                "div", attrs={"style": "display:inline-block; width:140px"})[0].text.strip() else 'Not yet Started'
            score_two = match.find_all(
                "div", attrs={"style": "display:inline-block; width:140px"})[1].text.strip() if match.find_all(
                "div", attrs={"style": "display:inline-block; width:140px"})[1].text.strip() else 'Not yet Started'
            team_one = match.find_all(
                "div", attrs={"class": "cb-ovr-flo cb-hmscg-tm-nm"})[0].text.strip()
            team_two = match.find_all(
                "div", attrs={"class": "cb-ovr-flo cb-hmscg-tm-nm"})[1].text.strip()
            match_id = match.find("a")["href"].split("/")[-1]
        
            embed.add_field(name=f"{team_names} - {status}", value=f"{team_one} - {score}\n{team_two} - {score_two}", inline=False)
        await ctx.reply(embed=embed)
    
    # @commands.command(name="subscribe_match", aliases=["sm"], help="Subscribe to a cricket match")
    # async def subscribe_match(self, ctx: Context):
    #     '''Subscribe to a cricket match'''

    #     self.subscribed = True
    #     self.subscribed_channel = ctx.channel.id
    #     await ctx.reply(f"Subscribed for live updates in {ctx.channel.mention}")
    
    # @commands.command(name="unsubscribe_match", aliases=["um"], help="Unsubscribe from a cricket match")
    # async def unsubscribe_match(self, ctx: Context, match_id: str):
    #     '''Unsubscribe from a cricket match'''
    #     self.subscribed = False
    #     self.subscribed_channel = None
    #     await ctx.reply(f"Unsubscribed from live updates in {ctx.channel.mention}")
    
    # #periodically send updates to subscribed channels
    # @commands.Cog.listener()
    # async def on_ready(self):
    #     '''Send updates to subscribed channels'''
    #     while self.subscribed:
    #         print("Checking for updates")
    #         channel = self.bot.get_channel(self.subscribed_channel)
    #         url = self.base_url + "cricket-match/live-scores"
    #         time.sleep(1)
    #         response = requests.get(url)
    #         soup = BeautifulSoup(response.content, 'html.parser')
    #         div = soup.find("div", attrs={"ng-show": "active_match_type == 'league-tab'"})
    #         matches = div.find_all(class_="cb-mtch-lst cb-col cb-col-100 cb-tms-itm")
    #         embed = discord.Embed(title="Live Cricket Scores", color=discord.Color.green())

    #         for match in matches:
    #             team_names = match.find("h3").text.strip().replace(",", "")
    #             status = match.find(
    #                 "div", attrs={"class": "cb-text-live"}).text.strip()
    #             score = match.find_all(
    #                 "div", attrs={"style": "display:inline-block; width:140px"})[0].text.strip() if match.find_all(
    #                 "div", attrs={"style": "display:inline-block; width:140px"})[0].text.strip() else 'Not yet Started'
    #             score_two = match.find_all(
    #                 "div", attrs={"style": "display:inline-block; width:140px"})[1].text.strip() if match.find_all(
    #                 "div", attrs={"style": "display:inline-block; width:140px"})[1].text.strip() else 'Not yet Started'
    #             team_one = match.find_all(
    #                 "div", attrs={"class": "cb-ovr-flo cb-hmscg-tm-nm"})[0].text.strip()
    #             team_two = match.find_all(
    #                 "div", attrs={"class": "cb-ovr-flo cb-hmscg-tm-nm"})[1].text.strip()
    #             match_id = match.find("a")["href"].split("/")[-1]
            
    #             embed.add_field(name=f"{team_names} - {status} {match_id}", value=f"{team_one} - {score}\n{team_two} - {score_two}", inline=False)
    #         await channel.send(embed=embed)    
    #     time.sleep(10)
    
async def setup(bot):
    await bot.add_cog(Cricket(bot))
    
