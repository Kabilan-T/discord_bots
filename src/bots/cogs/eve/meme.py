#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Maintaining Meme template commands '''

#-------------------------------------------------------------------------------

import os
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
        if not meme_data.startswith("http"):
            meme_data = self.bot.guild_path(guild_id, "meme_collection", meme_data)
        embed = discord.Embed(color=self.bot.default_color)
        file = discord.File(meme_data, filename="meme.png")
        embed.set_image(url=f"attachment://meme.png")
        await context.reply(embed=embed, file=file)
        self.bot.log.info(f"Inserted meme template: {meme_name} in {context.channel} for guild {guild_id}", context.guild)

    @commands.command(name="add_meme", description="Add a new meme template by attaching an image")
    async def add_meme(self, context: Context, *,meme_name: str):
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
        meme_dir = self.bot.guild_path(guild_id, "meme_collection")
        if not os.path.exists(meme_dir):
            os.makedirs(meme_dir)
        # Check if a URL is provided or an image is attached
        if context.message.attachments:
            attachment = context.message.attachments[0]
            meme_filename = f"{meme_name}.png"
            # Download and save the image
            await attachment.save(os.path.join(meme_dir, meme_filename))
            self.meme_templates[guild_id][meme_name] = meme_filename
        else:
            embed = discord.Embed(
                title="Invalid input",
                description="Please attach an image.",
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
    
    @commands.command(name="list_all_meme", description="List all meme templates in the collection")
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
        await context.send(embed=embed)
        for meme_name in self.meme_templates[guild_id]:
            embed = discord.Embed(
                title=meme_name,
                color=self.bot.default_color
            )
            meme_data = self.meme_templates[guild_id][meme_name]
            if not meme_data.startswith("http"):
                meme_data = self.bot.guild_path(guild_id, "meme_collection", meme_data)
            file = discord.File(meme_data, filename="meme.png")
            embed.set_thumbnail(url=f"attachment://meme.png")
            await context.send(embed=embed, files = [file])
            continue
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
            removed_meme_path = self.bot.guild_path(guild_id, "meme_collection", removed_meme)
            try:
                os.remove(removed_meme_path)
                self.bot.log.info(f"Removed image file {removed_meme_path} for meme {meme_name} in guild {guild_id}")
            except OSError as e:
                self.bot.log.warning(f"Failed to remove image file {removed_meme_path} for meme {meme_name} in guild {guild_id}: {e}")
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
            old_filename = self.meme_templates[guild_id][new_name]
            new_filename = f"{new_name}.png"
            old_file_path = self.bot.guild_path(guild_id, "meme_collection", old_filename)
            new_file_path = self.bot.guild_path(guild_id, "meme_collection", new_filename)
            os.rename(old_file_path, new_file_path)
            self.meme_templates[guild_id][new_name] = new_filename
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
        for guild_id in self.bot.list_guild_ids():
            guild_id = str(guild_id)
            self.meme_templates[guild_id] = self.bot.load_guild_yaml(guild_id, "meme_templates.yml")
            self.bot.log.info(f"Loaded meme templates for guild {guild_id}")

    def save_meme_templates(self, guild_id):
        """Save meme templates for a specific guild to a YAML file."""
        self.bot.save_guild_yaml(guild_id, "meme_templates.yml", self.meme_templates.get(guild_id, {}))
        self.bot.log.info(f"Saved meme templates for guild {guild_id}")

async def setup(bot):
    await bot.add_cog(Meme(bot))