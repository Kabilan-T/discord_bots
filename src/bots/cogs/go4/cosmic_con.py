#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' This cogs handles fun commands which has popculture references. '''

#-------------------------------------------------------------------------------

import os
import asyncio
import yaml
import discord
import typing
import random
import datetime
from pydub import AudioSegment
from pydub.generators import Sine
from discord.ext import commands
from discord.ext.commands import Context

tmp = "tmp"

class CosmicCon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.taunt = dict()
        self.taunt_gifs = ["https://tenor.com/view/willem-dafoe-laugh-crazy-car-gif-22580177",
                            "https://tenor.com/view/krillin-taunt-taunting-anime-dbz-gif-13298362",
                            "https://tenor.com/view/loafcat-meme-crypto-boxing-dance-gif-14735673580763849381",
                            "https://tenor.com/view/pithon-taunt-gif-12865791201436561590",
                            "https://tenor.com/view/pokemon-squirtle-taunt-gif-17959902",
                            "https://tenor.com/view/blegh-belt-the-croods-funny-face-tease-gif-19072929",
                            "https://tenor.com/view/jmthjk-gif-22224450",
                            "https://tenor.com/view/funny-silly-lion-king-gif-14287886"]
        
        self.foxy = dict()
        self.foxy_gifs = ["https://tenor.com/view/heypillagada-saipallavi-kali-gif-21578869",
                            "https://tenor.com/view/sarange-don-sivakarthikeyan-priyanka-mohan-gif-25621599",
                            "https://tenor.com/view/vinnaithandi-varuvaya-vtv-anbil-avan-trisha-jessie-gif-17836131",
                            "https://tenor.com/view/romantic-trending-neethaane-en-ponvasantham-samantha-akkineni-love-gif-7747061558216435844",
                            "https://tenor.com/view/meenakshi-chaudhary-bhibatsam-beautiful-angry-annoyed-gif-2262741861409338122",
                            "https://tenor.com/view/tara-in-okk-ok-bangaram-ok-kanmani-maniratnam-dulquer-gif-14768119681824719686",
                            "https://tenor.com/view/mrunal-thakur-hi-nanna-cute-smile-smirk-gif-4586904126258729553",
                            "https://tenor.com/view/janhvi-janhvi-kapoor-vogue-vogue-bffs-wink-gif-20008230"]
        
        self.linked_users = dict()
        self.ring_posessor = None


    ## Star Wars reference
    @commands.command(name='order66', description = "Exterminate all the Jedi from the Galactic Republic")
    @commands.has_permissions(administrator=True)
    async def order66(self, context: Context):
        ''' Ban all the users in the server'''
        # check if the user is the emperor (owner)
        if context.author.id != context.guild.owner_id:
            embed = discord.Embed(title="Order 66",
                                    description="Only the Emperor can execute Order 66",
                                    color=self.bot.default_color)
            await context.send(embed=embed)
            return
        # ask for confirmation
        embed = discord.Embed(title="Order 66",
                            description="Are you sure you want to execute **Order 66**?\nThis will ban all the users (Jedi) in the server (Galactic Republic).\n\nReact with ✅ to confirm.",
                                color=self.bot.default_color)
        message = await context.send(embed=embed)
        await message.add_reaction('✅')
        await message.add_reaction('❌')
        # wait for confirmation
        def check(reaction, user):
            return user == context.author and str(reaction.message.id) == str(message.id) and str(reaction.emoji) in ['✅', '❌']
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            embed = discord.Embed(title="Order 66",
                                description="Order 66 execution timed out",
                                color=self.bot.default_color)
            await message.edit(embed=embed)
            return
        # Abort Order 66
        if str(reaction.emoji) != '✅':
            embed = discord.Embed(title="Order 66",
                                description="Order 66 execution aborted",
                                color=self.bot.default_color)
            await message.edit(embed=embed)
            return
        # Execute Order 66
        embed = discord.Embed(title="Order 66",
                            description="It will be done, my Lord",
                            color=self.bot.default_color)
        await message.edit(embed=embed)
        for member in context.guild.members:
            # member not bot or not admin
            if not member.bot and not member.guild_permissions.administrator:
                await member.ban(reason="By the order of the Emperor")
        embed = discord.Embed(title="Order 66",
                            description="All the users (Jedi) have been banned",
                            color=self.bot.default_color)
        await context.send(embed=embed)
        self.bot.log.info(f"Order 66 executed by {context.author.name} in {context.guild.name}", context.guild)

    ## Thanos reference
    @commands.command(name='thanos_snap', description = "Eliminate half of the population from the known universe")
    @commands.has_permissions(administrator=True)
    async def snap(self, context: Context):
        ''' kick half of the users in the server '''
        # check if the user is the emperor (owner)
        if context.author.id != context.guild.owner_id:
            embed = discord.Embed(title="The Snap",
                                description="You need all the infinity stones to snap",
                                color=self.bot.default_color)
            await context.send(embed=embed)
            return
        # ask for confirmation
        embed = discord.Embed(title="The Snap :headstone:",
                            description="Are you sure you want to snap and ban half of the users in the server?\n\nReact with ✅ to confirm.",
                                color=self.bot.default_color)
        message = await context.send(embed=embed)
        await message.add_reaction('✅')
        await message.add_reaction('❌')
        def check(reaction, user):
            return user == context.author and str(reaction.message.id) == str(message.id) and str(reaction.emoji) in ['✅', '❌']
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            embed = discord.Embed(title="The Snap", 
                                description="The Snap execution timed out", 
                                color=self.bot.default_color)
            await message.edit(embed=embed)
            return
        # Abort Snap
        if str(reaction.emoji) != '✅':
            embed = discord.Embed(title="The Snap",
                                    description = "The Snap execution aborted",
                                    color=self.bot.default_color)
            await message.edit(embed=embed)
            return
        # Execute Snap
        embed = discord.Embed(title="The Snap",
                            description="I am inevitable",
                            color=self.bot.default_color)
        await message.edit(embed=embed)
        # Ban half of the users at random
        members = context.guild.members
        members = [member for member in members if not member.bot and not member.guild_permissions.administrator]
        for i, member in enumerate(members):
            if i % 2 == 0:
                await member.kick(reason=f"snapped by {context.author.name}")
        embed = discord.Embed(title="The Snap",
                            description="Perfectly balanced, as all things should be",
                            color=self.bot.default_color)
        await context.send(embed=embed)
        self.bot.log.info(f"The Snap executed by {context.author.name} in {context.guild.name}", context.guild)


    ## Harry Potter reference
    @commands.command(name='avada_kedavra', description = "Shutdown a muggle")
    @commands.has_permissions(administrator=True)
    async def avada_kedavra(self, context: Context, member: discord.Member):
        ''' disconnect a user from the voice channel '''
        if not context.author.guild_permissions.kick_members:
            embed = discord.Embed(title="Avada Kedavra",
                                description="You need to be a wizard to use this spell",
                                color=self.bot.default_color)
            await context.send(embed=embed)
            return
        if member.voice is not None:
            embed = discord.Embed(title="Avada Kedavra",
                                    description=f"{member.mention} is not in a voice channel",
                                    color=self.bot.default_color)
            await context.send(embed=embed)
            return
        await member.move_to(None)
        embed = discord.Embed(title="Avada Kedavra",
                                description=f"{member.mention} has been Sectumsempra'd",
                                color=self.bot.default_color) 
        await context.send(embed=embed)
        self.bot.log.info(f"Muggle {member.name} has been Avada Kedavra'd by {context.author.name} in {context.guild.name}", context.guild)

    @commands.command(name='wingardium_leviosa', aliases=['leviosa'], description = "throw a muggle away")
    async def wingardium_leviosa(self, context: Context, member: discord.Member):
        ''' Move a user to a different voice channel - 3 times with a delay '''
        if not context.author.guild_permissions.move_members:
            embed = discord.Embed(title="Wingardium Leviosa",
                                description="You need to practice more to use this spell",
                                color=self.bot.default_color)
            await context.send(embed=embed)
            return
        if member.voice is None:
            embed = discord.Embed(title="Wingardium Leviosa",
                                description=f"{member.mention} is not in a voice channel",
                                color=self.bot.default_color)
            await context.send(embed=embed)
            return
        original_channel = member.voice.channel
        voice_channels = context.guild.voice_channels
        voice_channels.remove(original_channel)
        voice_channels = random.sample(voice_channels, 3)
        for channel in voice_channels:
            await member.move_to(channel)
            await asyncio.sleep(3)
        await member.move_to(original_channel)
        embed = discord.Embed(title="Wingardium Leviosa",
                            description=f"{member.mention} has been thrown around",
                            color=self.bot.default_color)
        await context.send(embed=embed)
        self.bot.log.info(f"Muggle {member.name} has been Wingardium Leviosa'd by {context.author.name} in {context.guild.name}", context.guild)
    
    @commands.command(name='horcrux', description="Split a soul into multiple pieces")
    async def horcrux(self, context: commands.Context, soul_member: discord.Member, *horcruxes: discord.Member):
        """ As long as one of the horcruxes is alive, the soul member will be resurrected """
        if not context.author.guild_permissions.ban_members:
            embed = discord.Embed(title="Horcrux :snake:",
                                 description="You need to be a dark wizard to split your soul.",
                                 color=self.bot.default_color)
            await context.send(embed=embed)
            return
        horcruxes = [member.id for member in horcruxes if member.id != soul_member.id]
        guild_data_path = os.path.join(self.bot.data_dir, str(context.guild.id))
        horcrux_file_path = os.path.join(guild_data_path, 'horcruxes.yml')
        # Create guild directory if it doesn't exist
        if not os.path.exists(guild_data_path):
            os.makedirs(guild_data_path)
        # Load existing horcrux data (if any)
        horcrux_book = dict()
        if os.path.exists(horcrux_file_path):
            with open(horcrux_file_path, 'r') as file:
                try:
                    horcrux_book = yaml.safe_load(file) or dict()  # Ensure it loads as a dictionary
                except yaml.YAMLError:
                    horcrux_book = dict()
        # Update soul data
        if soul_member.id not in horcrux_book:
            horcrux_book[soul_member.id] = horcruxes
        else:
            existing_horcruxes = set(horcrux_book[soul_member.id])  # Prevent duplicates
            existing_horcruxes.update(horcruxes)
            horcrux_book[soul_member.id] = list(existing_horcruxes)
        # Save updated horcrux data
        with open(horcrux_file_path, 'w') as file:
            yaml.dump(horcrux_book, file, default_flow_style=False)

        embed = discord.Embed(title="Horcrux :snake:",
                            description=f"{soul_member.mention}'s soul has been split into {len(horcruxes)} pieces",
                            color=self.bot.default_color)
        await context.send(embed=embed)
        self.bot.log.info(f"{soul_member.name}'s soul has been split into {len(horcruxes)} pieces by {context.author.name} in {context.guild.name}", context.guild)

    async def refer_dark_book(self, member: discord.Member, guild: discord.Guild):
        ''' Check if the member is a horcrux '''
        guild_data_path = os.path.join(self.bot.data_dir, str(guild.id))
        horcrux_file_path = os.path.join(guild_data_path, 'horcruxes.yml')
        if not os.path.exists(horcrux_file_path):
            return False
        with open(horcrux_file_path, 'r') as file:
            try:
                horcrux_book = yaml.safe_load(file) or dict()  # Ensure it loads as a dictionary
            except yaml.YAMLError:
                horcrux_book = dict()
        # if member.id is not in keys, return False
        if member.id not in horcrux_book.keys():
            return False
        # Check if any of the horcruxes are alive
        for horcrux in horcrux_book[member.id]:
            if guild.get_member(horcrux) is not None:
                return True
        return False
    
    async def resurrect_the_soul(self, member: discord.Member, guild: discord.Guild):
        ''' Resurrect the member and send a invite '''
        # Unban the user if banned
        try:
            await guild.unban(member)
            self.bot.log.info(f"{member.name} has been unbanned in {guild.name} via Horcrux", guild)
        except discord.NotFound:
            self.bot.log.info(f"{member.name} is not banned in {guild.name}", guild)
        # Send an invite
        invite = await guild.text_channels[0].create_invite(max_uses=1, unique=True)
        self.bot.log.info(f"Invite {invite.url} created for {member.name} in {guild.name}", guild)
        try:
            embed = discord.Embed(title="Resurrection :wand:",
                                description=f"You have been resurrected in {guild.name}",
                                color=self.bot.default_color)
            embed.add_field(name="Join the world of the living :owl:", value=f"[Invite]({invite.url})")
            await member.send(embed=embed)
            self.bot.log.info(f"{member.name} has been resurrected in {guild.name} via Horcrux", guild)
        except discord.Forbidden:
            self.bot.log.info(f"Could not dm {member.name} in {guild.name}", guild)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        ''' Check if the member is a horcrux '''
        can_resurrect = await self.refer_dark_book(member, member.guild)
        if can_resurrect:
            self.bot.log.info(f"{member.name} has left {member.guild.name} but can be resurrected", member.guild)
            await self.resurrect_the_soul(member, member.guild)

    ## star trek reference
    @commands.command(name='beam_us', description = "Beam each_member to the different deck")
    async def beam_us(self, context: Context, channel: typing.Union[discord.VoiceChannel, int]):
        ''' Move all the users in the voice channel to a different voice channel '''
        if not context.author.guild_permissions.move_members:
            embed = discord.Embed(title="Beam us up :flying_saucer:",
                                description="You need to be a starfleet officer to use the transporter",
                                color=self.bot.default_color)
            await context.send(embed=embed)
            return
        if context.author.voice is None:
            embed = discord.Embed(title="Beam us up :flying_saucer:",
                                description="You need to be in a voice channel to use the transporter",
                                color=self.bot.default_color)
            await context.send(embed=embed)
            return
        if isinstance(channel, int):
            channel = context.guild.get_channel(channel)
            if channel is None:
                embed = discord.Embed(title="Beam us up :flying_saucer:",
                                    description="The destination deck does not exist",
                                    color=self.bot.default_color)
                await context.send(embed=embed)
                return
        members = context.author.voice.channel.members
        for member in members:
            await member.move_to(channel)
        embed = discord.Embed(title="Beam us up :flying_saucer:",
                            description=f"Everyone has been beamed to {channel.name}",
                            color=self.bot.default_color)
        await context.send(embed=embed)
        self.bot.log.info(f"Everyone has been beamed to {channel.name} by {context.author.name} in {context.guild.name}", context.guild)

    ## Naruto reference
    @commands.command(name='tsukuyomi', description = "Trap a shinobi in an illusion for 72 hours")
    async def tsukuyomi(self, context: Context, member: discord.Member):
        ''' Taunt a user for 72 hours wheneever they send a message '''
        if not context.author.guild_permissions.moderate_members:
            embed = discord.Embed(title="Tsukuyomi",
                                description="You need to be a chunin or higher to use this jutsu",
                                color=self.bot.default_color)
            await context.send(embed=embed)
            return
        self.taunt[member.id] = datetime.datetime.now(tz=datetime.timezone.utc)+datetime.timedelta(hours=72)
        embed = discord.Embed(title="Tsukuyomi",
                            description=f"{member.mention} has been trapped in the Tsukuyomi for next 72 hours",
                            color=self.bot.default_color)
        await context.send(embed=embed)
        self.bot.log.info(f"Shinobi {member.name} has been trapped in Tsukuyomi by {context.author.name} in {context.guild.name}", context.guild)

     ## Game cheat code reference
    @commands.command(name='foxy_magnet', description = "Atractive level 100")
    async def foxy_magnet(self, context: Context, member: discord.Member):
        ''' Send cute gifs to the user for 24 hours whenever they send a message '''
        if not context.author.guild_permissions.moderate_members:
            embed = discord.Embed(title="Foxy Magnet",
                                description="You need to be a pro gamer to use this cheat code",
                                color=self.bot.default_color)
            await context.send(embed=embed)
            return
        self.foxy[member.id] = datetime.datetime.now(tz=datetime.timezone.utc)+datetime.timedelta(hours=24)
        embed = discord.Embed(title="Foxy Magnet",
                            description=f"{member.mention} has been surrounded by gifs for next 24 hours",
                            color=self.bot.default_color)
        await context.send(embed=embed)
        self.bot.log.info(f"Player {member.name} has been surrounded by gifs by {context.author.name} in {context.guild.name}", context.guild)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        ''' Check if the user is taunted '''
        if message.author.id in self.taunt:
            if datetime.datetime.now(tz=datetime.timezone.utc) < self.taunt[message.author.id]:
                gif = random.choice(self.taunt_gifs)
                await message.reply(f"{gif}")
            else:
                self.taunt.pop(message.author.id, None)
                embed = discord.Embed(title="Tsukuyomi",
                                    description=f"{message.author.mention} has been released from the Tsukuyomi",
                                    color=self.bot.default_color)
                await message.channel.send(embed=embed)
                self.bot.log.info(f"Shinobi {message.author.name} has been released from Tsukuyomi", message.guild)

        if message.author.id in self.foxy:
            if datetime.datetime.now(tz=datetime.timezone.utc) < self.foxy[message.author.id]:
                gif = random.choice(self.foxy_gifs)
                await message.reply(f"{gif}")
            else:
                self.foxy.pop(message.author.id, None)
                embed = discord.Embed(title="Foxy Magnet",
                                    description=f"{message.author.mention} has been released from the Foxy Magnet",
                                    color=self.bot.default_color)
                await message.channel.send(embed=embed)
                self.bot.log.info(f"Player {message.author.name} has been released from Foxy Magnet", message.guild)

    ## R2D2 reference
    @commands.command(name='r2d2', description = "Translate a message to R2D2's language")
    async def r2d2(self, context: Context, *, message: str):
        ''' Translate the message to R2D2's language '''
        r2d2_message = [ f"{ord(char):08b}" for char in message]
        r2d2_message = ' '.join(r2d2_message)
        # Generate sound based on binary message
        beep = Sine(1000).to_audio_segment(duration=200)  # 1000Hz tone for '1'
        boop = Sine(500).to_audio_segment(duration=200)  # 500Hz tone for '0'
        final_audio = AudioSegment.silent(duration=0)
        for bit in r2d2_message:
            if bit == '1':
                final_audio += beep
            else:
                final_audio += boop
        audio_path = os.path.join(tmp, "translated.wav")
        final_audio.export(audio_path, format='wav')
        embed = discord.Embed(title="R2D2",
                                description="Beep Boop Beep!",
                                color=self.bot.default_color)
        await context.send(embed=embed)
        await context.send(file=discord.File(audio_path))
        os.remove(audio_path)
        self.bot.log.info(f"Message translated to R2D2's language by {context.author.name} in {context.guild.name}", context.guild)

    ## DragonBall Z reference
    @commands.command(name='fusion_dance', description = "Merge two saiyans into one")
    async def fusion_dance(self, context: Context, member1: discord.Member, member2: discord.Member):
        ''' Link voice states of two users together - 1 hr. If one moves/disconnects or mute/deafens, the other will follow '''
        if not context.author.guild_permissions.move_members:
            embed = discord.Embed(title="Fusion Dance :dragon:",
                                description="You need to be a super saiyan to perform the fusion dance",
                                color=self.bot.default_color)
            await context.send(embed=embed)
            return
        end_time = datetime.datetime.now(tz=datetime.timezone.utc)+datetime.timedelta(hours=1)
        self.linked_users[member1.id] = (member2.id, end_time)
        self.linked_users[member2.id] = (member1.id, end_time)
        embed = discord.Embed(title="Fusion Dance :dragon:",
                            description=f"{member1.mention} and {member2.mention} have been linked for next 1 hour",
                            color=self.bot.default_color)
        await context.send(embed=embed)
        self.bot.log.info(f"Saiyans {member1.name} and {member2.name} have been linked by {context.author.name} in {context.guild.name}", context.guild)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        ''' Check if the user is linked '''
        if member.id in self.linked_users.keys():
            linked_member_id, end_time = self.linked_users[member.id]
            linked_member = member.guild.get_member(linked_member_id)
            if datetime.datetime.now(tz=datetime.timezone.utc) < end_time:
                # Check if the linked member is also in a voice channel
                if linked_member.voice is None:
                    return
                if before.channel != after.channel:
                    await linked_member.move_to(after.channel)
                if before.self_mute != after.self_mute:
                    await linked_member.edit(mute=after.self_mute)
                if before.self_deaf != after.self_deaf:
                    await linked_member.edit(deafen=after.self_deaf)
            else:
                self.linked_users.pop(member.id, None)
                self.linked_users.pop(linked_member_id, None)
                embed = discord.Embed(title="Fusion Dance :dragon:",
                                    description=f"{member.mention} and {linked_member.mention} have been unlinked",
                                    color=self.bot.default_color)
                await after.channel.send(embed=embed)
                self.bot.log.info(f"Saiyans {member.name} and {linked_member.name} have been unlinked", member.guild)

    ## One Ring reference
    @commands.command(name='one_ring', description = "One ring to rule them all")
    async def one_ring(self, context: Context, possessor: discord.Member):
        ''' If the possessor moves/deafens/mutes, each_member in the guild will follow for 1 hour '''
        if not context.author.guild_permissions.move_members:
            embed = discord.Embed(title="One Ring :ring:",
                                description="You need to be the dark lord, Sauron to wield the one ring",
                                color=self.bot.default_color)
            await context.send(embed=embed)
            return
        end_time = datetime.datetime.now(tz=datetime.timezone.utc)+datetime.timedelta(hours=1)
        self.ring_posessor = {"id": possessor.id, "end_time": end_time}
        embed = discord.Embed(title="One Ring :ring:",
                            description=f"{possessor.mention} has been chosen as the ring bearer. Everyone follows the ring bearer for next 1 hour",
                            color=self.bot.default_color)
        await context.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        ''' Check if the user is the ring bearer '''
        if self.ring_posessor is None:
            return
        if member.id == self.ring_posessor["id"]:
            if datetime.datetime.now(tz=datetime.timezone.utc) < self.ring_posessor["end_time"]:
                for each_member in member.guild.members:
                    if each_member.voice is not None and each_member.id != member.id:
                        if before.channel != after.channel:
                            await each_member.move_to(after.channel)
                        if before.self_mute != after.self_mute:
                            await each_member.edit(mute=after.self_mute)
                        if before.self_deaf != after.self_deaf:
                            await each_member.edit(deafen=after.self_deaf)
            else:
                self.ring_posessor = None
                embed = discord.Embed(title="One Ring :ring:",
                                    description=f"{member.mention} has been relieved from the ring bearer duty",
                                    color=self.bot.default_color)
                await after.channel.send(embed=embed)
                self.bot.log.info(f"{member.name} has been relieved from the ring bearer duty", member.guild)

    ## Matrix reference
    @commands.has_permissions(manage_nicknames=True)
    @commands.command(name='glitch_in_the_matrix', description = "Who are you, really?")
    async def glitch_in_the_matrix(self, context: Context, *members: typing.Optional[discord.Member]):
        ''' Suffle the display names of the specified members or all online members '''
        if not members:
            members = [member for member in context.guild.members if member.status != discord.Status.offline and not member.bot]
        if not members:
            embed = discord.Embed(title="Glitch in the Matrix",
                                description="No members online to suffer from the glitch",
                                color=self.bot.default_color)
            await context.send(embed=embed)
            return
        # Shuffle the display names
        shuffled_names = random.sample([member.display_name for member in members], len(members))
        for member, new_name in zip(members, shuffled_names):
            try:
                await member.edit(nick=new_name)
            except discord.Forbidden:
                embed = discord.Embed(title="Glitch in the Matrix",
                                    description=f"{member.mention} is safe from the glitch (no permission to change nickname)",
                                    color=self.bot.default_color)
                await context.send(embed=embed)
                continue
            except discord.HTTPException:
                embed = discord.Embed(title="Glitch in the Matrix",
                                    description=f"{member.mention} could not be glitched (HTTP Exception)",
                                    color=self.bot.default_color)
                await context.send(embed=embed)
                continue
        embed = discord.Embed(title="Glitch in the Matrix",
                            description="Everyone's identity has been shuffled",
                            color=self.bot.default_color)
        await context.send(embed=embed)
        self.bot.log.info(f"Display names shuffled by {context.author.name} in {context.guild.name}", context.guild)

    @commands.has_permissions(manage_nicknames=True)
    @commands.command(name='reset_glitch', description = "Stabilize the Matrix")
    async def reset_glitch(self, context: Context):
        ''' Reset all display names to their original names '''
        members = [member for member in context.guild.members]
        if not members:
            embed = discord.Embed(title="Reset Glitch",
                                description="No members to reset",
                                color=self.bot.default_color)
            await context.send(embed=embed)
            return
        for member in members:
            try:
                await member.edit(nick=member.name)
            except discord.Forbidden:
                continue
            except discord.HTTPException:
                continue
        embed = discord.Embed(title="Reset Glitch",
                            description="Everyone's identity has been restored. The Matrix is stable again.",
                            color=self.bot.default_color)
        await context.send(embed=embed)
        self.bot.log.info(f"Display names reset by {context.author.name} in {context.guild.name}", context.guild)
    
    @commands.has_permissions(administrator=True)
    @commands.command(name='redpill_or_bluepill', description = "Choose your reality")
    async def redpill_or_bluepill(self, context: Context, member: discord.Member):
        ''' Give the user a choice between red pill and blue pill '''
        if not member or member.bot:
            embed = discord.Embed(title="Red Pill or Blue Pill",
                                description="You need to choose a valid member",
                                color=self.bot.default_color)
            await context.send(embed=embed)
            return
        embed = discord.Embed(title="Red Pill or Blue Pill",
                            description=f"{member.mention}, choose your reality:\nReact with 🔴 for Red Pill or 🔵 for Blue Pill",
                            color=self.bot.default_color)
        message = await context.send(f"{member.mention}", embed=embed)
        await message.add_reaction('🔴')
        await message.add_reaction('🔵')

        def check(reaction, user):
            return user == member and str(reaction.message.id) == str(message.id) and str(reaction.emoji) in ['🔴', '🔵']
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
        except asyncio.TimeoutError:
            embed = discord.Embed(title="Red Pill or Blue Pill",
                                description="You took too long to decide",
                                color=self.bot.default_color)
            await message.edit(embed=embed)
            return
        if str(reaction.emoji) == '🔴':
             # If the user chose red pill - kick them from the server but ask for confirmation
            self.bot.log.info(f"{member.name} chose Red Pill in {context.guild.name}", context.guild)
            embed = discord.Embed(title="Red Pill",
                                description=f"{member.mention} chose the Red Pill. They will be kicked from the server.\n\nReact with ✅ to confirm or ❌ to cancel.",
                                color=self.bot.default_color)
            message = await context.send(f"{context.author.mention}", embed=embed)
            await message.clear_reactions()
            await message.add_reaction('✅')
            await message.add_reaction('❌')

            def confirm_check(reaction, user):
                return user == context.author and str(reaction.message.id) == str(message.id) and str(reaction.emoji) in ['✅', '❌']

            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=confirm_check)
            except asyncio.TimeoutError:
                embed = discord.Embed(title="Red Pill",
                                    description="You took too long to decide",
                                    color=self.bot.default_color)
                await message.edit(embed=embed)
                return
            if str(reaction.emoji) != '✅':
                embed = discord.Embed(title="Red Pill",
                                    description="You chose not to kick the user",
                                    color=self.bot.default_color)
                await message.edit(embed=embed)
                return
            embed = discord.Embed(title="Red Pill",
                                description=f"{member.mention} will now experience the harsh reality of the Matrix.",
                                color=self.bot.default_color)
            await context.send(embed=embed)
            await member.kick(reason=f"Kicked by {context.author.name} for choosing Red Pill")
            self.bot.log.info(f"{member.name} has been kicked from {context.guild.name} for choosing Red Pill", context.guild)
        
        elif str(reaction.emoji) == '🔵':
            # If the user chose blue pill - give them a gift (one ring or horcrux) but ask for confirmation
            self.bot.log.info(f"{member.name} chose Blue Pill in {context.guild.name}", context.guild)
            embed = discord.Embed(title="Blue Pill",
                                description=f"{member.mention} chose the Blue Pill. They will receive a gift.\n\nReact with :ring: for temporary power or :snake: for eternal life.",
                                color=self.bot.default_color)
            message = await context.send(f"{context.author.mention}", embed=embed)
            await message.clear_reactions()
            await message.add_reaction('💍')
            await message.add_reaction('🐍')
            def gift_check(reaction, user):
                return user == context.author and str(reaction.message.id) == str(message.id) and str(reaction.emoji) in ['💍', '🐍']
            try:
                reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=gift_check)
            except asyncio.TimeoutError:
                embed = discord.Embed(title="Blue Pill",
                                    description="You took too long to decide",
                                    color=self.bot.default_color)
                await message.edit(embed=embed)
                return
            if str(reaction.emoji) == '💍':
                # If the user chose the ring - give them the one ring
                embed = discord.Embed(title="One Ring",
                                    description=f"{member.mention} has been given the One Ring. They will have temporary power for 1 hour.",
                                    color=self.bot.default_color)
                await message.edit(embed=embed)
                await self.one_ring(context, member)
                return
            elif str(reaction.emoji) == '🐍':
                # If the user chose the horcrux - give them a horcrux
                embed = discord.Embed(title="Horcrux :snake:",
                                    description=f"{member.mention} has been given a Horcrux. They will have eternal life as long as the horcrux exists.",
                                    color=self.bot.default_color)
                await message.edit(embed=embed)
                await self.horcrux(context, member, *context.guild.members)
                return
            

        

async def setup(bot):
    await bot.add_cog(CosmicCon(bot))