#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Bingo game for the bot'''

#-------------------------------------------------------------------------------

import typing 
import random
import asyncio
import discord
from discord.ext import commands
from discord.ext.commands import Context
import matplotlib.pyplot as plt
from io import BytesIO


class Bingo(commands.Cog, name="Bingo"):
    def __init__(self, bot):
        '''Initializes the bingo cog'''
        self.bot = bot
        self.games = {}  # Store active games

    @commands.command(name="bingo", description="Start a game of bingo.")
    async def bingo(self, context: Context, add_bot: typing.Optional[bool] = True, *players: discord.Member):
        '''Starts a game of bingo'''
        self.bot.log.info(f"Bingo game requested by {context.author.name}", context.guild)
        # Check if players are mentioned
        if not 1 <= len(players):
            embed = discord.Embed(
                title="No players mentioned",
                description=f"Use `{self.bot.prefix[context.guild.id]}bingo <@player>...` to start a game of bingo.",
                color=self.bot.default_color,
                )
            self.bot.log.warning(f"Failed to start a game in #{context.channel.name} of {context.guild.name} as no players were mentioned.", context.guild)
            await context.send(embed=embed)
            return
        
        # Check it is possible to send DMs to players send a game start message
        for player in players:
            if player.bot:
                embed = discord.Embed(
                    title="Ooops! You invited a bot :slight_frown:",
                    description=f"Only humans can play bingo. {player.mention} is a bot. Aborting game.",
                    color=self.bot.default_color,
                    )
                await context.send(embed=embed)
                self.bot.log.warning(f"Game aborted. {player.name} is a bot.", context.guild)
                return
            try:
                embed = discord.Embed(
                    title="BinGo! :smiley:",
                    description=f"You have been invited to play bingo by {context.author.mention}.",
                    color=self.bot.default_color,
                    )
                await player.send(embed=embed)
            except discord.Forbidden:
                embed = discord.Embed(
                    title="Ooops! Game aborted :slight_frown:",
                    description=f"Please enable DMs from server members to play bingo.\n{player.mention} has DMs disabled.",
                    color=self.bot.default_color,
                    )
                await context.send(embed=embed)
                self.bot.log.warning(f"Game aborted. {player.name} has DMs disabled.", context.guild)
                return

        # Create new game
        game_id = str(context.guild.id) + str(context.channel.id)
        if game_id in self.games:
            embed = discord.Embed(
                title="Ooops! Game already started",
                description=f"There is already an active game in this channel. :slight_frown:",
                color=self.bot.default_color,
                )
            await context.send(embed=embed)
            self.bot.log.info(f"Failed to start a game in #{context.channel.name} of {context.guild.name} but a game is already active.", context.guild)
            return
        else:
            self.games[game_id] = {
                "players": players,
                "numbers": [i for i in range(1, 25)],
                "called_numbers": [],
                "current_number": None,
                "current_player": None,
                "channel": context.channel,
                "game_over": False,
                "chart": {},
                "score": {},
                "score_limit": 5,
                "winners": []
            }
            embed = discord.Embed(
                title="BinGo! :smiley:",
                description=f"Game started by {context.author.mention}.\n {' '.join([player.mention for player in players])} are playing.\n Let's see who gets bingo first! :slight_smile:",
                color=self.bot.default_color,
                )
            await context.send(embed=embed)
            if add_bot:
                self.games[game_id]["players"] = players + (self.bot.user,)
                embed = discord.Embed(
                    title=self.bot.user.name + " joined the game! :smiley:",
                    description=f"I'll also play the game with you guys. Let's see who wins! :slight_smile:",
                    color=self.bot.default_color,
                    )
                await context.send(embed=embed)
            self.bot.log.info(f"Game started in #{context.channel.name} of {context.guild.name} with players {', '.join([player.name for player in self.games[game_id]['players']])}.", context.guild)
            await self.create_game(game_id)    
        
        # Play the game
        while game_id in self.games and not self.games[game_id]["game_over"]:
            await self.play_game(game_id)
            if game_id not in self.games:
                return
        
        # Game over
        await self.end_game(game_id)
        embed = discord.Embed(
            title="Thanks for playing! :slight_smile:",
            description=f"{' '.join([player.mention for player in self.games[game_id]['players']])} \nSee you next time!",
            color=self.bot.default_color,
            )
        await context.send(embed=embed)
        del self.games[game_id]
        self.bot.log.info(f"Game ended in #{context.channel.name} of {context.guild.name}.", context.guild)
    
    @commands.command(name="quit", description="Quit the current game of bingo.")
    async def quit(self, context: Context):
        '''Quits the current game of bingo'''
        game_id = str(context.guild.id) + str(context.channel.id)
        if game_id in self.games:
            if context.author in self.games[game_id]["players"]:
                embed = discord.Embed(
                    title="Game aborted! :slight_frown:",
                    description=f"{context.author.mention} quit the game.",
                    color=self.bot.default_color,
                    )
                self.games[game_id]["game_over"] = True
                await context.send(embed=embed)
                del self.games[game_id]
                self.bot.log.info(f"Game aborted in #{context.channel.name} of {context.guild.name} by {context.author.name}.", context.guild)
            else:
                embed = discord.Embed(
                    title="Ooops! :slight_frown:",
                    description=f"You are not playing the game.",
                    color=self.bot.default_color,
                    )
                await context.send(embed=embed)
                self.bot.log.warning(f"Failed to abort game in #{context.channel.name} of {context.guild.name} by {context.author.name} as they are not playing.", context.guild)
        else:
            embed = discord.Embed(
                title="Ooops! :slight_frown:",
                description=f"There is no active game in this channel.",
                color=self.bot.default_color,
                )
            await context.send(embed=embed)
            self.bot.log.warning(f"Failed to abort game in #{context.channel.name} of {context.guild.name} by {context.author.name} as there is no active game.", context.guild)
    
    async def create_game(self, game_id):
        for player in self.games[game_id]["players"]:
            self.games[game_id]["chart"][player.id] = self.create_bingo_chart()
            self.games[game_id]["score"][player.id] = 0
            embed = discord.Embed(
                title="Bingo charts are ready. :smiley:",
                description=f"Your Bingo Chart:",
                color=self.bot.default_color,
                )
            board = self.format_bingo_chart(self.games[game_id]['chart'][player.id])
            file = discord.File(board, filename="bingo_chart.png")
            embed.set_image(url="attachment://bingo_chart.png")
            if player != self.bot.user:
                await player.send(embed=embed, file=file)
        self.games[game_id]["current_player"] = self.games[game_id]["players"][0]

    async def end_game(self, game_id):
        for player in self.games[game_id]["players"]:
            if player in self.games[game_id]["winners"]:
                embed = discord.Embed(
                    title="Congratulations! :smiley:",
                    description=f"You won the game! :tada:",
                    color=self.bot.default_color,
                    )
                if player != self.bot.user:
                    await player.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="Ooops! :slight_frown:",
                    description=f"You lost the game! Better luck next time.",
                    color=self.bot.default_color,
                    )
                if player != self.bot.user:
                    await player.send(embed=embed)
        embed = discord.Embed(
            title="Game over! :smiley:",
            description=f"{' '.join([player.mention for player in self.games[game_id]['winners']])} won the game! :tada:",
            color=self.bot.default_color,
            )
        await self.games[game_id]["channel"].send(embed=embed)
        self.bot.log.info(f"Game in #{self.games[game_id]['channel'].name} of {self.games[game_id]['channel'].guild.name} ended.", self.games[game_id]["channel"].guild)
        self.bot.log.info(f"Winners: {[player.name for player in self.games[game_id]['winners']]}", self.games[game_id]["channel"].guild)
        self.bot.log.info(f"Players - Scores: {[(player.name, self.games[game_id]['score'][player.id]) for player in self.games[game_id]['players']]}", self.games[game_id]["channel"].guild)
    
    async def play_game(self, game_id):
        embed = discord.Embed(
            title="It's your turn to play! :smiley:",
            description=f"Your Bingo Chart:",
            color=self.bot.default_color,
            )
        board = self.format_bingo_chart(self.games[game_id]['chart'][self.games[game_id]['current_player'].id])
        file = discord.File(board, filename="bingo_chart.png")
        embed.set_image(url="attachment://bingo_chart.png")
        if self.games[game_id]["current_player"] != self.bot.user:
            await self.games[game_id]["current_player"].send(embed=embed, file=file)
        self.bot.log.info(f"Game in #{self.games[game_id]['channel'].name} of {self.games[game_id]['channel'].guild.name} - {self.games[game_id]['current_player'].name}'s turn.", self.games[game_id]["channel"].guild)

        for player in self.games[game_id]["players"]:
            if player != self.games[game_id]["current_player"]:
                embed = discord.Embed(
                    title=f"It's {self.games[game_id]['current_player'].display_name}'s turn to play! :smiley:",
                    description=f"Let's wait for them to finish.",
                    color=self.bot.default_color,
                    )
                if player != self.bot.user:
                    await player.send(embed=embed)
        
        # Wait for the current player to call a number
        is_number_called = await self.call_number(self.games[game_id]["current_player"], game_id)
        if game_id not in self.games:
            return
        if is_number_called:
            self.games[game_id]["called_numbers"].append(self.games[game_id]["current_number"])
            self.bot.log.info(f"Game in #{self.games[game_id]['channel'].name} of {self.games[game_id]['channel'].guild.name} - {self.games[game_id]['current_player'].name} called {self.games[game_id]['current_number']}.", self.games[game_id]["channel"].guild)
            score_updated = False
            for player in self.games[game_id]["players"]:
                # strike the number from all players' charts
                self.games[game_id]["chart"][player.id] = self.strike_number(self.games[game_id]["chart"][player.id], self.games[game_id]["current_number"])
                # update the score
                score = self.get_score(self.games[game_id]["chart"][player.id])
                if score > self.games[game_id]["score"][player.id]:
                    self.games[game_id]["score"][player.id] = score
                    score_updated = True
                if player != self.games[game_id]["current_player"]:
                    embed = discord.Embed(
                        title=f"{self.games[game_id]['current_player'].display_name} called {self.games[game_id]['current_number']}!",
                        description=f"Your Bingo Chart:",
                        color=self.bot.default_color,
                        )
                    board = self.format_bingo_chart(self.games[game_id]['chart'][player.id])
                    file = discord.File(board, filename="bingo_chart.png")
                    embed.set_image(url="attachment://bingo_chart.png")
                    if player != self.bot.user:
                        await player.send(embed=embed, file=file)
                elif player == self.games[game_id]["current_player"]:
                    embed = discord.Embed(
                        title=f"You called {self.games[game_id]['current_number']}!",
                        description=f"Your Bingo Chart:",
                        color=self.bot.default_color,
                        )
                    board = self.format_bingo_chart(self.games[game_id]['chart'][player.id])
                    file = discord.File(board, filename="bingo_chart.png")
                    embed.set_image(url="attachment://bingo_chart.png")
                    if player != self.bot.user:
                        await player.send(embed=embed, file=file)
        
            if score_updated:
                embed = discord.Embed(
                    title="Scores updated! :smiley:",
                    description=f"{self.get_scores_message(game_id)}",
                    color=self.bot.default_color,
                    )
                await self.games[game_id]["channel"].send(embed=embed)
                for player in self.games[game_id]["players"]:
                    if player != self.bot.user:
                        await player.send(embed=embed)
                    if self.games[game_id]["score"][player.id] >= self.games[game_id]["score_limit"]:
                        self.games[game_id]["game_over"] = True
                        self.games[game_id]["winners"].append(player)
        
        # Change current player
        self.games[game_id]["current_player"] = self.games[game_id]["players"][(self.games[game_id]["players"].index(self.games[game_id]["current_player"])+1) % len(self.games[game_id]["players"])]

    async def call_number(self, player, game_id):
        if player == self.bot.user:
            return self.bot_move(game_id)
        embed = discord.Embed(  
            title="Call a number :hourglass_flowing_sand:",
            description=f"Please send a number from your chart to call it.",
            color=self.bot.default_color,
            )
        await player.send(embed=embed)
        try:
            message = await self.bot.wait_for("message",
                                              timeout=30,
                                              check=lambda message: message.author == player and message.channel == player.dm_channel and game_id in self.games
            )
            if game_id not in self.games:
                return False
            number = int(message.content)
            if not self.is_number_valid(number, game_id):
                embed = discord.Embed(
                    title="Invalid number :confused:",
                    description=f"Please send a number from your chart to call it.",
                    color=self.bot.default_color,
                    )
                await player.send(embed=embed)
                return await self.call_number(player, game_id)
            self.games[game_id]["current_number"] = number
            return True
        except asyncio.TimeoutError:
            if game_id not in self.games:
                return False
            embed = discord.Embed(
                title="Ooops! Time's up :slight_frown:",
                description=f"You took too long to call a number. You turn is skipped.",
                color=self.bot.default_color,
                )
            await player.send(embed=embed)
            return False

    def bot_move(self, game_id):
        chart = self.games[game_id]["chart"][self.bot.user.id].copy()
        # search for a number which can increase the score
        available_moves = []
        for row in chart:
            for number in row:
                if number > 0 and number not in self.games[game_id]["called_numbers"]:
                    available_moves.append(number)
        number = self.get_wise_number(chart, available_moves)
        self.games[game_id]["current_number"] = number
        return True
    
    def get_wise_number(self, chart, available_moves):
        max_score = 0
        wise_number = random.choice(available_moves)
        for number in available_moves:
            score = self.get_score(self.strike_number(chart, number))
            if score > max_score:
                max_score = score
                wise_number = number
        return wise_number
        
    def create_bingo_chart(self):
        numbers = list(range(1, 26))
        random.shuffle(numbers)
        return [numbers[i:i + 5] for i in range(0, 25, 5)]
    
    def is_number_valid(self, number, game_id):
        if number in self.games[game_id]["called_numbers"]:
            return False
        # Check if number is in the current player's chart
        for row in self.games[game_id]["chart"][self.games[game_id]["current_player"].id]:
            if number in row:
                return True
        return False
    
    def strike_number(self, chart, number):
        return [[-cell if cell == number else cell for cell in row] for row in chart]

    def get_score(self, chart):
        score = 0
        # Check rows
        score += sum(all(cell < 0 for cell in row) for row in chart)
        # Check columns
        score += sum(all(row[i] < 0 for row in chart) for i in range(5))
        # Check diagonals
        score += all(chart[i][i] < 0 for i in range(5))
        score += all(chart[i][4 - i] < 0 for i in range(5))
        return score
    
    def format_bingo_chart(self, chart):
        table_data = []
        for row in chart:
            table_data.append([str(cell) if cell > 0 else 'X' for cell in row])
        fig, ax = plt.subplots(figsize=(2, 2))
        ax.axis('off')
        colors = ['#0000A0','#ADD8E6']  # Light blue and dark blue
        table = ax.table(cellText=table_data, loc='center', cellLoc='center', colWidths=[0.1]*5, 
                        cellColours=[[colors[0] if table_data[i][j] == 'X' else colors[1] for j in range(5)] for i in range(5)])
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(2, 2)
        # Hide axes
        ax.axis('off')
        # Save the figure to a buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        plt.close(fig)
        buffer.seek(0)
        return buffer
    
    def get_scores_message(self, game_id):
        message = str()
        max_score = max(self.games[game_id]["score"].values())
        for player in self.games[game_id]["players"]:
            score = self.games[game_id]["score"][player.id]
            message += f'{player .mention}: ({score}) :\t'
            message += " ".join([f"***~~{letter}~~***" if i < score else f"**{letter}**" for i, letter in enumerate('BINGO')])
            if score == max_score:
                message += "\t:crown:"
            message += "\n"
        return message
    

async def setup(bot):
    await bot.add_cog(Bingo(bot))