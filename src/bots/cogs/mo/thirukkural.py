#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Thirukkural related commands '''

#-------------------------------------------------------------------------------

import os
import yaml
import discord
import typing
import datetime
import pandas as pd
from discord.ext import tasks
from discord.ext import commands
from discord.ext.commands import Context

class Thirukkural(commands.Cog, name="Thirukkural"):
    def __init__(self, bot):
        self.bot = bot
        self.kurals = self.load_kurals()
        self.daily_kural.start()

    def load_kurals(self):
        data_path = os.path.join(self.bot.data_dir, "thirukkural_dataset.csv")
        if not os.path.exists(data_path):
            self.bot.log.warning(f"Thirukkural data file not found at {data_path}")
            return None
        try:
            df = pd.read_csv(data_path)
            return df
        except Exception as e:
            self.bot.log.warning(f"Error loading Thirukkural data: {e}")
            return None

    @tasks.loop(time=datetime.time(hour=0, minute=0, second=10, tzinfo=datetime.timezone.utc))
    async def daily_kural(self):
        if self.kurals is None or self.kurals.empty:
            self.bot.log.warning("No Kurals available to send.")
            return
        kural = self.kurals.sample(n=1).iloc[0]
        kural['Verse'] = kural['Verse'].replace("\t\t", "\n")
        kural['Translation'] = kural['Translation'].replace("\n", " ")
        embed = discord.Embed(
            title=f"Thirukkural - {kural['Section Name']} ({kural['Chapter Name']})",
            description=f"**{kural['Verse']}**\n\n*{kural['Translation']}*\n\n{kural['Explanation']}",
            color=self.bot.default_color,
        )
        for guild in self.bot.guilds:
            channel = discord.utils.find(lambda c: "general" in c.name.lower(), guild.text_channels)
            if channel:
                await channel.send(embed=embed)
                self.bot.log.info(f"Sent daily Thirukkural to {guild.name} in {channel.name}", guild)
            else:
                self.bot.log.warning(f"No general channel found in {guild.name}", guild)

    @daily_kural.before_loop
    async def before_daily_kural(self):
        await self.bot.wait_until_ready()

    def cog_unload(self):
        self.daily_kural.cancel()

    @commands.command(name='kural', description="Get a specific Kural by number")
    async def get_kural(self, context, number: int):
        if self.kurals is None or self.kurals.empty:
            embed = discord.Embed(
                title="Thirukkural",
                description="Kural dataset is not available.",
                color=self.bot.default_color,
            )
            await context.send(embed=embed)
            self.bot.log.warning("Kural dataset is not available.", context.guild)
            return
        if number < 1 or number > len(self.kurals):
            embed = discord.Embed(
                title="Thirukkural",
                description="Invalid Kural number. Please enter a number between 1 and 1330.",
                color=self.bot.default_color,
            )
            await context.send(embed=embed)
            self.bot.log.warning("Invalid Kural number entered by user.", context.guild)
            return
        kural = self.kurals.iloc[number - 1]
        kural['Verse'] = kural['Verse'].replace("\t\t", "\n")
        embed = discord.Embed(
            title=f"Thirukkural #{number} - {kural['Section Name']} ({kural['Chapter Name']})",
            description=f"**{kural['Verse']}**\n\n*{kural['Explanation']}*",
            color=self.bot.default_color,
        )
        await context.send(embed=embed)
        self.bot.log.info(f"Sent Kural #{number} to {context.guild.name}", context.guild)
    
    @commands.command(name='list_adhigarams', description="List all Adhigarams in Thirukkural")
    async def list_adhigarams(self, context):
        if self.kurals is None or self.kurals.empty:
            embed = discord.Embed(
                title="Thirukkural",
                description="Kural dataset is not available.",
                color=self.bot.default_color,
            )
            await context.send(embed=embed)
            self.bot.log.warning("Kural dataset is not available.", context.guild)
            return
        chapter_names = self.kurals['Chapter Name'].unique()
        adhigaram_count = 0
        for chapter in chapter_names:
            adhigarams = self.kurals[self.kurals['Chapter Name'] == chapter]['Section Name'].unique()
            embed = discord.Embed(
                title=f"Thirukkural - {chapter}",
                description="",
                color=self.bot.default_color,
            )
            for adhigaram in adhigarams:
                embed.description = f"{embed.description}\n{adhigaram_count + 1}. {adhigaram}"
                adhigaram_count += 1
            await context.send(embed=embed)
        self.bot.log.info(f"Sent list of Adhigarams to {context.guild.name}", context.guild)

    @commands.command(name='adhigaram', description="Get all Kurals in a specific Adhigaram")
    async def get_adhigaram(self, context, *, section_name_or_number: typing.Union[int, str]):
        if isinstance(section_name_or_number, int):
            if section_name_or_number < 1 or section_name_or_number > 133:
                embed = discord.Embed(
                    title="Thirukkural",
                    description="Invalid Adhigaram number. Please enter a number between 1 and 133.",
                    color=self.bot.default_color,
                )
                await context.send(embed=embed)
                self.bot.log.warning("Invalid Adhigaram number entered by user.", context.guild)
                return
            section_name = self.kurals['Section Name'].unique()[section_name_or_number-1]
        else:
            section_name = section_name_or_number
        if self.kurals is None or self.kurals.empty:
            embed  = discord.Embed(
                title="Thirukkural",
                description="Kural dataset is not available.",
                color=self.bot.default_color,
            )
            await context.send(embed=embed)
            self.bot.log.warning("Kural dataset is not available.", context.guild)
            return
        kurals = self.kurals[self.kurals['Section Name'].str.lower() == section_name.lower()]
        if kurals.empty:
            embed = discord.Embed(
                title="Thirukkural",
                description="Invalid Adhigaram name. Please enter a valid Adhigaram name.",
                color=self.bot.default_color,
            )
            await context.send(embed=embed)
            self.bot.log.warning("Invalid Adhigaram name entered by user.", context.guild)
            return
        chapter_name = kurals.iloc[0]['Chapter Name']
        embed = discord.Embed(
            title=f"Thirukkural - {section_name} ({chapter_name})",
            color=self.bot.default_color,
        )
        for _, kural in kurals.iterrows():
            kural['Verse'] = kural['Verse'].replace("\t\t", "\n")
            embed.add_field(
                name=f"Kural #{kural.name + 1}",
                value=f"**{kural['Verse']}**\n\n*{kural['Explanation']}*",
                inline=False
            )
        await context.send(embed=embed)
        self.bot.log.info(f"Sent Adhigaram {section_name} to {context.guild.name}", context.guild)

async def setup(bot):
    await bot.add_cog(Thirukkural(bot))