#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Maintaining Meme template commands '''

#-------------------------------------------------------------------------------

import os
import yaml
import regex
import asyncio
import discord
from fuzzywuzzy import process
from discord.ext import commands
from discord.ext.commands import Context

class Meme(commands.Cog, name="Meme Maintainer"):
    def __init__(self, bot):
        self.bot = bot
        self.meme_templates = dict()
        self.load_meme_templates()  # Load memes on startup

    @commands.command( name="insert", description="Insert a meme template")
    async def insert_meme(self, context: Context, *, meme_name: str):
        """Insert meme template."""
        guild_id = str(context.guild.id)
        meme_name = meme_name.lower()
        self.bot.log.info(f"{context.author} requested to insert meme template: {meme_name} in {context.channel} for guild {guild_id}", context.guild)
        # Check if the guild has any meme templates
        if guild_id not in self.meme_templates:
            embed = discord.Embed(
                title="No memes found :confused:",
                description=f"Sorry, there are no meme templates available for this guild.",
                color=self.bot.default_color
            )
            await context.reply(embed=embed)
            self.bot.log.warning(f"No meme templates found for guild {guild_id}", context.guild)
            return
        closest_match = process.extractOne(meme_name, self.meme_templates[guild_id].keys())
        if closest_match[1] < 60:
            embed = discord.Embed(
                title="Meme not found :confused:",
                description=f"Sorry, I couldn't find any meme template similar to `{meme_name}`",
                color=self.bot.default_color
            )
            await context.reply(embed=embed)
            self.bot.log.warning(f"Couldn't find meme template similar to {meme_name} in guild {guild_id}", context.guild)
            return
        meme_data = self.meme_templates[guild_id][closest_match[0]]
        embed = discord.Embed(color=self.bot.default_color)
        if meme_data.startswith("http"):
            embed.set_image(url=meme_data)
        else:
            file = discord.File(meme_data, filename="meme.png")
            embed.set_image(url=f"attachment://meme.png")
            await context.reply(embed=embed, file=file)
            return
        await context.reply(embed=embed)
        self.bot.log.info(f"Inserted meme template: {meme_name} in {context.channel} for guild {guild_id}", context.guild)

    @commands.command(name="add_meme", description="Add a new meme template either by URL or by attaching an image")
    async def add_meme(self, context: Context, meme_name: str, meme_url: str = None):
        """Add a new meme template."""
        guild_id = str(context.guild.id)
        meme_name = meme_name.lower()
        # Initialize meme_templates for the guild if not present
        if guild_id not in self.meme_templates:
            self.meme_templates[guild_id] = {}
        # Check if meme already exists
        if meme_name in self.meme_templates[guild_id]:
            embed = discord.Embed(
                title="Meme already exists",
                description=f"A meme with the name `{meme_name}` already exists in this guild.",
                color=self.bot.default_color
            )
            await context.reply(embed=embed)
            self.bot.log.warning(f"Meme with the name {meme_name} already exists in guild {guild_id}", context.guild)
            return
        guild_path = os.path.join(self.bot.data_dir, guild_id)
        meme_dir = os.path.join(guild_path, "meme_collection")
        if not os.path.exists(meme_dir):
            os.makedirs(meme_dir)
        # Check if a URL is provided or an image is attached
        if meme_url:
            self.meme_templates[guild_id][meme_name] = meme_url
        elif context.message.attachments:
            attachment = context.message.attachments[0]
            file_path = os.path.join(meme_dir, f"{meme_name}.png")
            # Download and save the image
            await attachment.save(file_path)
            self.meme_templates[guild_id][meme_name] = file_path
        else:
            embed = discord.Embed(
                title="Invalid input",
                description="Please provide a meme URL or attach an image.",
                color=self.bot.default_color
            )
            await context.reply(embed=embed)
            self.bot.log.warning(f"Invalid input while adding meme {meme_name} for guild {guild_id}", context.guild)
            return
        self.save_meme_templates(guild_id)
        embed = discord.Embed(
            title="Meme added!",
            description=f"Meme `{meme_name}` has been added successfully to this guild.",
            color=self.bot.default_color
        )
        await context.reply(embed=embed)
        self.bot.log.info(f"Added new meme template: {meme_name} in guild {guild_id}", context.guild)
    
    @commands.command(name="list_memes", description="List all meme templates in the collection")
    async def list_memes(self, context: Context):
        """List all meme templates."""
        guild_id = str(context.guild.id)
        # Check if the guild has any meme templates
        if guild_id not in self.meme_templates or not self.meme_templates[guild_id]:
            embed = discord.Embed(
                title="No memes found :confused:",
                description=f"Sorry, there are no meme templates available for this guild.",
                color=self.bot.default_color
            )
            await context.reply(embed=embed)
            self.bot.log.warning(f"No meme templates found for guild {guild_id}", context.guild)
            return
        embed = discord.Embed(
            title="Meme templates",
            description="Here are all the meme templates available in this guild:",
            color=self.bot.default_color
        )
        for meme_name in self.meme_templates[guild_id]:
            embed.add_field(name=meme_name, value=self.meme_templates[guild_id][meme_name], inline=False)
        await context.reply(embed=embed)
        self.bot.log.info(f"Listed meme templates for guild {guild_id}", context.guild)

    @commands.command(name="remove_meme", description="Remove an existing meme from the collection")
    async def remove_meme(self, context: Context, *, meme_name: str):
        """Remove an existing meme template."""
        guild_id = str(context.guild.id)
        meme_name = meme_name.lower()
        # Check if the guild has any meme templates
        if guild_id not in self.meme_templates or meme_name not in self.meme_templates[guild_id]:
            embed = discord.Embed(
                title="Meme not found :confused:",
                description=f"Sorry, I couldn't find any meme template with the name `{meme_name}` in this guild.",
                color=self.bot.default_color
            )
            await context.reply(embed=embed)
            self.bot.log.warning(f"Couldn't find meme template {meme_name} in guild {guild_id} for removal", context.guild)
            return
        # Remove the meme template
        removed_meme = self.meme_templates[guild_id].pop(meme_name)
        # Delete the associated image file if it's not a URL
        if not removed_meme.startswith("http"):
            try:
                os.remove(removed_meme)
                self.bot.log.info(f"Removed image file {removed_meme} for meme {meme_name} in guild {guild_id}")
            except OSError as e:
                self.bot.log.warning(f"Failed to remove image file {removed_meme} for meme {meme_name} in guild {guild_id}: {e}")
        # Save the updated meme templates
        self.save_meme_templates(guild_id)
        embed = discord.Embed(
            title="Meme removed!",
            description=f"Meme `{meme_name}` has been removed successfully from this guild.",
            color=self.bot.default_color
        )
        await context.reply(embed=embed)
        self.bot.log.info(f"Removed meme template {meme_name} in guild {guild_id}", context.guild)

    @commands.command(name="rename_meme", description="Rename an existing meme from the collection")
    async def rename_meme(self, context: Context, old_name: str, new_name: str):
        """Rename an existing meme template."""
        guild_id = str(context.guild.id)
        old_name = old_name.lower()
        new_name = new_name.lower()
        # Check if the old name exists and the new name doesn't conflict with an existing meme
        if guild_id not in self.meme_templates or old_name not in self.meme_templates[guild_id]:
            embed = discord.Embed(
                title="Meme not found :confused:",
                description=f"Sorry, I couldn't find any meme template with the name `{old_name}` in this guild.",
                color=self.bot.default_color
            )
            await context.reply(embed=embed)
            self.bot.log.warning(f"Couldn't find meme template {old_name} in guild {guild_id} for renaming", context.guild)
            return
        if new_name in self.meme_templates[guild_id]:
            embed = discord.Embed(
                title="Name conflict :confused:",
                description=f"A meme with the name `{new_name}` already exists in this guild. Please choose a different name.",
                color=self.bot.default_color
            )
            await context.reply(embed=embed)
            self.bot.log.warning(f"Name conflict while renaming {old_name} to {new_name} in guild {guild_id}", context.guild)
            return
        # Rename the meme
        self.meme_templates[guild_id][new_name] = self.meme_templates[guild_id].pop(old_name)
        # Rename the associated image file if it's not a URL
        if not self.meme_templates[guild_id][new_name].startswith("http"):
            old_file_path = self.meme_templates[guild_id][new_name]
            new_file_path = os.path.join(os.path.dirname(old_file_path), f"{new_name}.png")
            os.rename(old_file_path, new_file_path)
            self.meme_templates[guild_id][new_name] = new_file_path
            self.bot.log.info(f"Renamed image file from {old_file_path} to {new_file_path} for meme {new_name} in guild {guild_id}")
        # Save the updated meme templates
        self.save_meme_templates(guild_id)
        embed = discord.Embed(
            title="Meme renamed!",
            description=f"Meme `{old_name}` has been renamed to `{new_name}` successfully in this guild.",
            color=self.bot.default_color
        )
        await context.reply(embed=embed)
        self.bot.log.info(f"Renamed meme template {old_name} to {new_name} in guild {guild_id}", context.guild)

    def load_meme_templates(self):
        """Load meme templates for each guild from YAML files."""
        if os.path.exists(self.bot.data_dir):
            guilds = os.listdir(self.bot.data_dir)
            for guild_id in guilds:
                fpath = os.path.join(self.bot.data_dir, guild_id, "meme_templates.yml")
                if os.path.exists(fpath):
                    with open(fpath, 'r') as file:
                        self.meme_templates[guild_id] = yaml.safe_load(file) or {}
                        self.bot.log.info(f"Loaded meme templates for guild {guild_id} from `{fpath}`")
                else:
                    self.bot.log.info(f"No meme templates found for guild {guild_id}")

    def save_meme_templates(self, guild_id):
        """Save meme templates for a specific guild to a YAML file."""
        guild_path = os.path.join(self.bot.data_dir, guild_id)
        if not os.path.exists(guild_path):
            os.makedirs(guild_path)
            self.bot.log.info(f"Created directory for guild {guild_id} at {guild_path}")
        fpath = os.path.join(guild_path, "meme_templates.yml")
        with open(fpath, 'w+') as file:
            yaml.dump(self.meme_templates.get(guild_id, {}), file)
            self.bot.log.info(f"Saved meme templates for guild {guild_id} to `{fpath}`")

async def setup(bot):
    await bot.add_cog(Meme(bot))