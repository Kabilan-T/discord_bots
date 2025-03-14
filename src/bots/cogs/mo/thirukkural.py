#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Thirukkural related commands '''

#-------------------------------------------------------------------------------

import os
import json
import random
import typing
import discord
import datetime
from discord.ext import tasks
from discord.ext import commands
from discord.ext.commands import Context

class Thirukkural(commands.Cog, name="Thirukkural"):
    def __init__(self, bot):
        self.bot = bot
        self.kurals = self.load_kurals()
        self.daily_kural.start()

    def load_kurals(self):
        """ Load Thirukkural data from JSON file """
        data_path = os.path.join(self.bot.data_dir, "thirukkural.json")
        if not os.path.exists(data_path):
            self.bot.log.warning(f"Thirukkural data file not found at {data_path}")
            return None
        try:
            with open(data_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            return data['kural']
        except Exception as e:
            self.bot.log.warning(f"Error loading Thirukkural data: {e}")
            return None

    @tasks.loop(time=datetime.time(hour=0, minute=0, second=10, tzinfo=datetime.timezone.utc))
    async def daily_kural(self):
        if not self.kurals:
            self.bot.log.warning("No Kurals available to send.")
            return
        kural = random.choice(self.kurals)
        embed = discord.Embed(
            title=f"Thirukkural #{kural['Number']} - {kural['adikaram_name']} ({kural['paul_name']})",
            description=f"**{kural['Line1']}\n{kural['Line2']}**",
            color=self.bot.default_color,
        )
        embed.add_field(name=f"Transliteration #{kural['Number']} - {kural['adikaram_transliteration']} ({kural['paul_transliteration']})", value=f"{kural['transliteration1']}\n{kural['transliteration2']}", inline=False)
        embed.add_field(name=f"Translation #{kural['Number']} - {kural['adikaram_translation']} ({kural['paul_translation']})", value=f"{kural['Translation']}", inline=False)
        embed.add_field(name="Explanation", value=f"Mu Karunanidhi : {kural['mk']} \nEnglish : {kural['explanation']}", inline=False)
        embed.add_field(name="Couplet", value=kural['couplet'], inline=False)
        
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
        if not self.kurals:
            embed = discord.Embed(
                title="Thirukkural", 
                description="Kural dataset is not available.", 
                color=self.bot.default_color)
            await context.send(embed=embed)
            self.bot.log.warning("Kural dataset is not available.", context.guild)
            return
        if number < 1 or number > len(self.kurals):
            embed = discord.Embed(
                title="Thirukkural", 
                description="Invalid Kural number. Please enter a number between 1 and 1330.", 
                color=self.bot.default_color)
            await context.send(embed=embed)
            self.bot.log.warning(f"Invalid Kural number: {number}", context.guild)
            return
        kural = self.kurals[number - 1]
        embed = discord.Embed(
            title=f"Thirukkural #{kural['Number']} - {kural['adikaram_name']} ({kural['paul_name']})",
            description=f"**{kural['Line1']}\n{kural['Line2']}**",
            color=self.bot.default_color,
        )
        embed.add_field(name=f"Transliteration #{kural['Number']} - {kural['adikaram_transliteration']} ({kural['paul_transliteration']})", value=f"{kural['transliteration1']}\n{kural['transliteration2']}", inline=False)
        embed.add_field(name=f"Translation #{kural['Number']} - {kural['adikaram_translation']} ({kural['paul_translation']})", value=f"{kural['Translation']}", inline=False)
        embed.add_field(name="Explanation", value=f"Mu Karunanidhi : {kural['mk']} \nEnglish : {kural['explanation']}", inline=False)
        embed.add_field(name="Couplet", value=kural['couplet'], inline=False)
        await context.send(embed=embed)
        self.bot.log.info(f"Sent Kural {number} to {context.channel.name}", context.guild)

    @commands.command(name='random_kural', description="Get a random Kural optionally from a specific paul")
    async def get_random_kural(self, context, paul: typing.Optional[typing.Union[int, str]] = None):
        if not self.kurals:
            embed = discord.Embed(
                title="Thirukkural", 
                description="Kural dataset is not available.", 
                color=self.bot.default_color)
            await context.send(embed=embed)
            self.bot.log.warning("Kural dataset is not available.", context.guild)
            return
        if paul is not None:
            if isinstance(paul, int):
                paul_name = set(k['paul_name'] for k in self.kurals)[paul - 1]
            else:
                paul_name = paul
            if paul_name not in [k['paul_name'] for k in self.kurals]:
                embed = discord.Embed(
                    title="Thirukkural", 
                    description="Invalid Paul name. Please enter a valid Paul name.", 
                    color=self.bot.default_color)
                await context.send(embed=embed)
                self.bot.log.warning(f"Invalid Paul name: {paul_name}", context.guild)
                return
            kurals = [k for k in self.kurals if k['paul_name'] == paul_name]
        else:
            kurals = self.kurals
        kural = random.choice(kurals)
        embed = discord.Embed(
            title=f"Thirukkural #{kural['Number']} - {kural['adikaram_name']} ({kural['paul_name']})",
            description=f"**{kural['Line1']}\n{kural['Line2']}**",
            color=self.bot.default_color,
        )
        embed.add_field(name=f"Transliteration #{kural['Number']} - {kural['adikaram_transliteration']} ({kural['paul_transliteration']})", value=f"{kural['transliteration1']}\n{kural['transliteration2']}", inline=False)
        embed.add_field(name=f"Translation #{kural['Number']} - {kural['adikaram_translation']} ({kural['paul_translation']})", value=f"{kural['Translation']}", inline=False)
        embed.add_field(name="Explanation", value=f"Mu Karunanidhi : {kural['mk']} \nEnglish : {kural['explanation']}", inline=False)
        embed.add_field(name="Couplet", value=kural['couplet'], inline=False)
        await context.send(embed=embed)
        self.bot.log.info(f"Sent random Kural to {context.channel.name}", context.guild)
    
    @commands.command(name='adhigaram', description="Get all Kurals in a specific Adhigaram")
    async def get_adhigaram(self, context, *, adhigaram_no_or_name: typing.Union[int, str]):
        if not self.kurals:
            embed = discord.Embed(title="Thirukkural", description="Kural dataset is not available.", color=self.bot.default_color)
            await context.send(embed=embed)
            self.bot.log.warning("Kural dataset is not available.", context.guild)
            return
        if isinstance(adhigaram_no_or_name, int):
            adhigaram_no = adhigaram_no_or_name
            if adhigaram_no < 1 or adhigaram_no > 133:
                embed = discord.Embed(title="Thirukkural", description="Invalid Adhigaram number. Please enter a number between 1 and 133.", color=self.bot.default_color)
                await context.send(embed=embed)
                self.bot.log.warning(f"Invalid Adhigaram number: {adhigaram_no}", context.guild)
                return
            adhigaram_name = self.kurals[adhigaram_no * 10 - 10]['adikaram_name']
        else:
            adhigaram_name = adhigaram_no_or_name
            if adhigaram_name not in [k['adikaram_name'] for k in self.kurals]:
                embed = discord.Embed(title="Thirukkural", description="Invalid Adhigaram name. Please enter a valid Adhigaram name.", color=self.bot.default_color)
                await context.send(embed=embed)
                self.bot.log.warning(f"Invalid Adhigaram name: {adhigaram_name}", context.guild)
                return
            adhigaram_no = [k['adikaram_name'] for k in self.kurals].index(adhigaram_name) // 10 + 1
        paul_name = self.kurals[adhigaram_no * 10 - 10]['paul_name']
        kurals = [k for k in self.kurals if k['adikaram_name'] == adhigaram_name]
        embed = discord.Embed(
            title=f"Thirukkural Adhigaram {adhigaram_no} - {adhigaram_name} ({paul_name})",
            description="",
            color=self.bot.default_color,
        )
        for kural in kurals:
            embed.add_field(name=f"#{kural['Number']}\n{kural['Line1']}\n{kural['Line2']}", value=f"Mu Karunanidhi : {kural['mk']}", inline=False)
        await context.send(embed=embed)
        self.bot.log.info(f"Sent Adhigaram {adhigaram_no} - {adhigaram_name} to {context.channel.name}", context.guild)

    @commands.command(name='adhigaram_en', description="Get all Kurals in a specific Adhigaram in English")
    async def get_adhigaram_en(self, context, *, adhigaram_no_or_name: typing.Union[int, str]):
        if not self.kurals:
            embed = discord.Embed(title="Thirukkural", description="Kural dataset is not available.", color=self.bot.default_color)
            await context.send(embed=embed)
            self.bot.log.warning("Kural dataset is not available.", context.guild)
            return
        if isinstance(adhigaram_no_or_name, int):
            adhigaram_no = adhigaram_no_or_name
            if adhigaram_no < 1 or adhigaram_no > 133:
                embed = discord.Embed(title="Thirukkural", description="Invalid Adhigaram number. Please enter a number between 1 and 133.", color=self.bot.default_color)
                await context.send(embed=embed)
                self.bot.log.warning(f"Invalid Adhigaram number: {adhigaram_no}", context.guild)
                return
            adhigaram_name = self.kurals[adhigaram_no * 10 - 10]['adikaram_transliteration']
        else:
            adhigaram_name = adhigaram_no_or_name
            if adhigaram_name not in [k['adikaram_transliteration'] for k in self.kurals]:
                embed = discord.Embed(title="Thirukkural", description="Invalid Adhigaram name. Please enter a valid Adhigaram name.", color=self.bot.default_color)
                await context.send(embed=embed)
                self.bot.log.warning(f"Invalid Adhigaram name: {adhigaram_name}", context.guild)
                return
            adhigaram_no = [k['adikaram_transliteration'] for k in self.kurals].index(adhigaram_name) // 10 + 1
        paul_name = self.kurals[adhigaram_no * 10 - 10]['paul_transliteration']
        kurals = [k for k in self.kurals if k['adikaram_transliteration'] == adhigaram_name]
        adhigaram_translation = self.kurals[adhigaram_no * 10 - 10]['adikaram_translation']
        paul_translation = self.kurals[adhigaram_no * 10 - 10]['paul_translation']
        embed = discord.Embed(
            title=f"Thirukkural Adhigaram {adhigaram_no} - {adhigaram_name} ({paul_name})",
            description=f"{adhigaram_translation} ({paul_translation})",
            color=self.bot.default_color,
        )
        for kural in kurals:
            embed.add_field(name=f"#{kural['Number']}\n{kural['transliteration1']}\n{kural['transliteration2']}", value=f"Explanation : {kural['explanation']}", inline=False)
        await context.send(embed=embed)
        self.bot.log.info(f"Sent Adhigaram in English {adhigaram_no} - {adhigaram_name} to {context.channel.name}", context.guild)

    @commands.command(name='list_all_adhigarams', description="List all Adhigarams")
    async def list_all_adhigarams(self, context):
        if not self.kurals:
            embed = discord.Embed(title="Thirukkural", description="Kural dataset is not available.", color=self.bot.default_color)
            await context.send(embed=embed)
            self.bot.log.warning("Kural dataset is not available.", context.guild)
            return
        pauls = list(dict.fromkeys([k['paul_name'] for k in self.kurals]))
        adhigaram_no = 1
        for paul in pauls:
            adhigarams = set(k['adikaram_name'] for k in self.kurals if k['paul_name'] == paul)
            embed = discord.Embed(
                title=f"Thirukkural Adhigarams - {paul} - ({len(adhigarams)})",
                description= "\n".join([f"{num}. {adhigaram}" for num, adhigaram in enumerate(adhigarams, adhigaram_no)]),
                color=self.bot.default_color,
            )        
            adhigaram_no += len(adhigarams)
            await context.send(embed=embed)
        self.bot.log.info(f"Sent list of all Adhigarams to {context.channel.name}", context.guild)

    @commands.command(name='list_all_adhigarams_en', description="List all Adhigarams in English")
    async def list_all_adhigarams_en(self, context):
        if not self.kurals:
            embed = discord.Embed(title="Thirukkural", description="Kural dataset is not available.", color=self.bot.default_color)
            await context.send(embed=embed)
            self.bot.log.warning("Kural dataset is not available.", context.guild)
            return
        pauls = list(dict.fromkeys([k['paul_transliteration'] for k in self.kurals]))
        paul_translations = list(dict.fromkeys([k['paul_translation'] for k in self.kurals]))
        adhigaram_no = 1
        for paul, paul_translation in zip(pauls, paul_translations):
            adhigarams = set(k['adikaram_transliteration'] for k in self.kurals if k['paul_transliteration'] == paul)
            adhigaram_translations = set(k['adikaram_translation'] for k in self.kurals if k['paul_transliteration'] == paul)
            paul_translation = self.kurals[adhigaram_no * 10 - 10]['paul_translation']
            embed = discord.Embed(
                title=f"Thirukkural Adhigarams - {paul} - {paul_translation} ({len(adhigarams)})",
                description= "\n".join([f"{num}. {adhigaram} ({adhigaram_translation})" for num, (adhigaram, adhigaram_translation) in enumerate(zip(adhigarams, adhigaram_translations), adhigaram_no)]),
                color=self.bot.default_color,
            )
            adhigaram_no += len(adhigarams)
            await context.send(embed=embed)
        self.bot.log.info(f"Sent list of all Adhigarams in English to {context.channel.name}", context.guild)

async def setup(bot):
    await bot.add_cog(Thirukkural(bot))