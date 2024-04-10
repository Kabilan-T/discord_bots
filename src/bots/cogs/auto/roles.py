#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Role management features such as adding and removing roles '''

#-------------------------------------------------------------------------------

import os
import yaml
import discord
from discord.ext import commands
from discord.ext.commands import Context

class Roles(commands.Cog, name="Roles"):
    def __init__(self, bot):
        '''Initializes the role cog'''
        self.bot = bot
        self.role_channel = dict()
        self.default_role = dict()
        self.reaction_roles = dict()
        self.read_config()
        self.read_reaction_roles()

    @commands.command(name="set_default_role", description="Set the default role for the new members joining the server")
    @commands.has_permissions(administrator=True)
    async def setdefaultrole(self, context: Context, role: discord.Role):
        '''Set the default role for the new members joining the server'''
        self.default_role[context.guild.id] = role.id
        if os.path.exists(os.path.join(self.bot.data_dir, str(context.guild.id), "config.yaml")):
            with open(os.path.join(self.bot.data_dir, str(context.guild.id), "config.yaml"), "r") as file:
                config = yaml.load(file, Loader=yaml.FullLoader)
            config["default_role"] = role.id
            with open(os.path.join(self.bot.data_dir, str(context.guild.id), "config.yaml"), "w+") as file:
                yaml.dump(config, file)
        else:
            with open(os.path.join(self.bot.data_dir, str(context.guild.id), "config.yaml"), "w+") as file:
                yaml.dump({"default_role": role.id}, file)
        self.bot.log.info(f"Default role set to {role.name} by {context.author.name}", context.guild)
        embed = discord.Embed(
            title="Default Role Set",
            description=f"Default role set to {role.mention}",
            color=self.bot.default_color,
            )
        await context.send(embed=embed)

    @commands.command(name="set_role_channel", description="Set the channel for reaction roles")
    @commands.has_permissions(administrator=True)
    async def setrolechannel(self, context: Context, channel: discord.TextChannel):
        '''Set the channel for reaction roles'''
        self.role_channel[context.guild.id] = channel.id
        if os.path.exists(os.path.join(self.bot.data_dir, str(context.guild.id), "config.yaml")):
            with open(os.path.join(self.bot.data_dir, str(context.guild.id), "config.yaml"), "r") as file:
                config = yaml.load(file, Loader=yaml.FullLoader)
            config["role_channel"] = channel.id
            with open(os.path.join(self.bot.data_dir, str(context.guild.id), "config.yaml"), "w+") as file:
                yaml.dump(config, file)
        else:
            with open(os.path.join(self.bot.data_dir, str(context.guild.id), "config.yaml"), "w+") as file:
                yaml.dump({"role_channel": channel.id}, file)
        self.bot.log.info(f"Role channel set to {channel.mention} by {context.author.name}", context.guild)
        embed = discord.Embed(
            title="Role Channel Set",
            description=f"Role channel set to {channel.mention}",
            color=self.bot.default_color,
            )
        await context.send(embed=embed)
        
    @commands.command(name="add_reaction_role", description="Add a role to the reaction roles")
    @commands.has_permissions(administrator=True)
    async def addrole(self, context: Context, message: str, role: discord.Role, emoji: str):
        '''Add a role to the reaction roles'''
        if context.guild.id not in self.role_channel.keys():
            embed = discord.Embed(
                title="Role Channel Not Set",
                description="Please set the role channel and try again",
                color=discord.Color.red(),
                )
            await context.send(embed=embed)
            return
        if context.guild.id not in self.reaction_roles.keys():
            self.reaction_roles[context.guild.id] = dict()
        channel = context.guild.get_channel(self.role_channel[context.guild.id])
        embed = discord.Embed(
            title=f"React to get the {role.name} role",
            description=message,
            color=self.bot.default_color,
            )
        message = await channel.send(embed=embed)
        await message.add_reaction(emoji)
        self.reaction_roles[context.guild.id][message.id] = {"role": role.id, "emoji": emoji}
        with open(os.path.join(self.bot.data_dir, str(context.guild.id), "reaction_roles.yaml"), "w+") as file:
            yaml.dump(self.reaction_roles[context.guild.id], file)
        self.bot.log.info(f"Reaction role {role.name} with emoji {emoji} added by {context.author.name}", context.guild)
        embed = discord.Embed(
            title="Reaction Role Added",
            description=f"Reaction role added for {role.mention}",
            color=discord.Color.green(),
            )
        await context.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        '''Add default role to the new member'''
        if member.bot:
            return
        if member.guild.id in self.default_role.keys():
            role = member.guild.get_role(self.default_role[member.guild.id])
            await member.add_roles(role)
            self.bot.log.info(f"Default community role {role.name} added to {member.display_name}", member.guild)
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        '''Add role to the member when they react to the message'''
        if payload.guild_id in self.reaction_roles.keys():
            if payload.message_id in self.reaction_roles[payload.guild_id].keys():
                guild = self.bot.get_guild(payload.guild_id)
                role = guild.get_role(self.reaction_roles[payload.guild_id][payload.message_id]["role"])
                emoji = self.reaction_roles[payload.guild_id][payload.message_id]["emoji"]
                if str(payload.emoji) != emoji:
                    return
                member = guild.get_member(payload.user_id)
                await member.add_roles(role)
                self.bot.log.info(f"Role {role.name} added to {member.display_name} by reacting to the message", guild)
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        '''Remove role from the member when they remove the reaction'''
        if payload.guild_id in self.reaction_roles.keys():
            if payload.message_id in self.reaction_roles[payload.guild_id].keys():
                guild = self.bot.get_guild(payload.guild_id)
                role = guild.get_role(self.reaction_roles[payload.guild_id][payload.message_id]["role"])
                emoji = self.reaction_roles[payload.guild_id][payload.message_id]["emoji"]
                if str(payload.emoji) != emoji:
                    return
                member = guild.get_member(payload.user_id)
                await member.remove_roles(role)
                self.bot.log.info(f"Role {role.name} removed from {member.display_name} by removing the reaction", guild)
        
    def read_config(self):
        if os.path.exists(os.path.join(self.bot.data_dir)):
            guilds = os.listdir(self.bot.data_dir)
            for guild_id in guilds:
                if os.path.exists(os.path.join(self.bot.data_dir, guild_id, "config.yaml")):
                    with open(os.path.join(self.bot.data_dir, guild_id, "config.yaml"), "r") as file:
                        config = yaml.load(file, Loader=yaml.FullLoader)
                    self.role_channel[int(guild_id)] = config.get("role_channel")
                    self.default_role[int(guild_id)] = config.get("default_role") 
    
    def read_reaction_roles(self):
        if os.path.exists(os.path.join(self.bot.data_dir)):
            guilds = os.listdir(self.bot.data_dir)
            for guild_id in guilds:
                if os.path.exists(os.path.join(self.bot.data_dir, guild_id, "reaction_roles.yaml")):
                    with open(os.path.join(self.bot.data_dir, guild_id, "reaction_roles.yaml"), "r") as file:
                        reaction_roles = yaml.load(file, Loader=yaml.FullLoader)
                    self.reaction_roles[int(guild_id)] = reaction_roles


async def setup(bot):
    await bot.add_cog(Roles(bot))