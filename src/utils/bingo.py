#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Bingo game for the bot'''

#-------------------------------------------------------------------------------

import discord
from discord.ext import commands
from discord.ext.commands import Context
import random
import asyncio


class Bingo(commands.Cog, name="Bingo"):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}  # Store active games

    @commands.command(name="bingo", description="Start a game of bingo.")
    async def bingo(self, context: Context, *players: discord.Member):
        self.logger.info(f"Bingo game requested by {context.author.name}")
        # Check if players are mentioned
        if not 1 <= len(players):
            embed = discord.Embed(
                title="No players mentioned",
                description=f"Use `{self.bot.prefix}bingo <@player>...` to start a game of bingo.",
                color=0xBEBEFE,
            )
            print("Game started")
            await context.send(embed=embed)
            return
        
        # Check it is possible to send DMs to players send a game start message
        for player in players:
            try:
                embed = discord.Embed(
                    title="BinGo! :smiley:",
                    description=f"You have been invited to play bingo by {context.author.mention}.",
                    color=0xBEBEFE,
                )
                await player.send(embed=embed)
            except discord.Forbidden:
                embed = discord.Embed(
                    title="Ooops! Game aborted :slight_frown:",
                    description=f"Please enable DMs from server members to play bingo.\n{player.mention} has DMs disabled.",
                    color=0xBEBEFE,
                )
                await context.send(embed=embed)
                self.logger.info(f"Game aborted. {player.name} has DMs disabled.")
                return

        # Create new game
        game_id = str(context.guild.id) + str(context.channel.id)
        if game_id in self.games:
            embed = discord.Embed(
                title="Ooops! Game already started",
                description=f"There is already an active game in this channel. :slight_frown:",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
            self.logger.info(f"Failed to start a game in #{context.channel.name} of {context.guild.name} but a game is already active.")
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
            await self.create_game(self.games[game_id])
            embed = discord.Embed(
                title="BinGo! :smiley:",
                description=f"Game started by {context.author.mention}.\n {' '.join([player.mention for player in players])} are playing.\n Let's see who gets bingo first! :slight_smile:",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
            self.logger.info(f"Game started in #{context.channel.name} of {context.guild.name} with players {[player.name for player in players]}.")
        
        # Play the game
        while not self.games[game_id]["game_over"]:
            await self.play_game(self.games[game_id])
        
        # Game over
        await self.end_game(self.games[game_id])
        embed = discord.Embed(
            title="Thanks for playing! :slight_smile:",
            description=f"{' '.join([player.mention for player in self.games[game_id]['players']])} \nSee you next time!",
            color=0xBEBEFE,
        )
        await context.send(embed=embed)
        del self.games[game_id]
        self.logger.info(f"Game ended in #{context.channel.name} of {context.guild.name}.")
    
    @commands.command(name="quit", description="Quit the current game of bingo.")
    async def quit(self, context: Context):
        game_id = str(context.guild.id) + str(context.channel.id)
        if game_id in self.games:
            if context.author in self.games[game_id]["players"]:
                embed = discord.Embed(
                    title="Game aborted! :slight_frown:",
                    description=f"{context.author.mention} quit the game.",
                    color=0xBEBEFE,
                )
                await context.send(embed=embed)
                del self.games[game_id]
                self.logger.info(f"Game aborted in #{context.channel.name} of {context.guild.name} by {context.author.name}.")
            else:
                embed = discord.Embed(
                    title="Ooops! :slight_frown:",
                    description=f"You are not playing the game.",
                    color=0xBEBEFE,
                )
                await context.send(embed=embed)
                self.logger.info(f"Failed to abort game in #{context.channel.name} of {context.guild.name} by {context.author.name} as they are not playing.")
        else:
            embed = discord.Embed(
                title="Ooops! :slight_frown:",
                description=f"There is no active game in this channel.",
                color=0xBEBEFE,
            )
            await context.send(embed=embed)
            self.logger.info(f"Failed to abort game in #{context.channel.name} of {context.guild.name} by {context.author.name} as there is no active game.")
    
    async def create_game(self, game):
        for player in game["players"]:
            game["chart"][player.id] = self.create_bingo_chart()
            game["score"][player.id] = 0
            embed = discord.Embed(
                title="Your bingo chart is ready. :smiley:",
                description=f"{self.format_bingo_chart(game['chart'][player.id])}",
                color=0xBEBEFE,
            )
            await player.send(embed=embed)
        game["current_player"] = game["players"][0]

    async def end_game(self, game):
        for player in game["players"]:
            if player in game["winners"]:
                embed = discord.Embed(
                    title="Congratulations! :smiley:",
                    description=f"You won the game! :tada:",
                    color=0xBEBEFE,
                )
                await player.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="Ooops! :slight_frown:",
                    description=f"You lost the game! Better luck next time.",
                    color=0xBEBEFE,
                )
                await player.send(embed=embed)
        embed = discord.Embed(
            title="Game over! :smiley:",
            description=f"{' '.join([player.mention for player in game['winners']])} won the game! :tada:",
            color=0xBEBEFE,
        )
        await game["channel"].send(embed=embed)
        self.logger.info(f"Game in #{game['channel'].name} of {game['channel'].guild.name} ended.")
        self.logger.info(f"Winners: {[player.name for player in game['winners']]}")
        self.logger.info(f"Players - Scores: {[(player.name, game['score'][player.id]) for player in game['players']]}")
    
    async def play_game(self, game):
        # send a message to the current player
        embed = discord.Embed(
            title="It's your turn to play! :smiley:",
            description=f"Your Bingo Chart:\n{self.format_bingo_chart(game['chart'][game['current_player'].id])}",
            color=0xBEBEFE,
        )
        await game["current_player"].send(embed=embed)
        self.logger.info(f"Game in #{game['channel'].name} of {game['channel'].guild.name} - {game['current_player'].name}'s turn.")

        for player in game["players"]:
            if player != game["current_player"]:
                embed = discord.Embed(
                    title=f"It's {game['current_player'].mention}'s turn to play!",
                    description=f"Let's wait for them to finish.",
                    color=0xBEBEFE,
                )
                await player.send(embed=embed)
        
        # Wait for the current player to call a number
        is_number_called = await self.call_number(game["current_player"], game)
        if is_number_called:
            game["called_numbers"].append(game["current_number"])
            self.logger.info(f"Game in #{game['channel'].name} of {game['channel'].guild.name} - {game['current_player'].name} called {game['current_number']}.")
            score_updated = False
            for player in game["players"]:
                # strike the number from all players' charts
                game["chart"][player.id] = self.strike_number(game["chart"][player.id], game["current_number"])
                # update the score
                score = self.get_score(game["chart"][player.id])
                if score > game["score"][player.id]:
                    game["score"][player.id] = score
                    score_updated = True
                if player != game["current_player"]:
                    embed = discord.Embed(
                        title=f"{game['current_player'].mention} called {game['current_number']}!",
                        description=f"Your Bingo Chart:\n{self.format_bingo_chart(game['chart'][player.id])}",
                        color=0xBEBEFE,
                    )
                    await player.send(embed=embed)
                elif player == game["current_player"]:
                    embed = discord.Embed(
                        title=f"You called {game['current_number']}!",
                        description=f"Your Bingo Chart:\n{self.format_bingo_chart(game['chart'][player.id])}",
                        color=0xBEBEFE,
                    )
                    await player.send(embed=embed)
        
        if score_updated:
            embed = discord.Embed(
                title="Scores updated! :smiley:",
                description=f"{self.get_scores_message(game)}",
                color=0xBEBEFE,
            )
            await game["channel"].send(embed=embed)
            for player in game["players"]:
                await player.send(embed=embed)
                if game["score"][player.id] >= game["score_limit"]:
                    game["game_over"] = True
                    game["winners"].append(player)
        
        # Change current player
        game["current_player"] = game["players"][(game["players"].index(game["current_player"])+1) % len(game["players"])]

    async def call_number(self, player, game):
        embed = discord.Embed(  
            title="Call a number :hourglass_flowing_sand:",
            description=f"Please send a number from your chart to call it.",
            color=0xBEBEFE,
        )
        await player.send(embed=embed)
        try:
            message = await self.bot.wait_for("message",  timeout=60,
                check=lambda message: message.author == player and message.channel == player.dm_channel,
               
            )
            number = int(message.content)
            if self.is_number_valid(number, game):
                game["current_number"] = number
                return True
            else:
                embed = discord.Embed(
                    title="Invalid number :confused:",
                    description=f"Please send a number from your chart to call it.",
                    color=0xBEBEFE,
                )
                await player.send(embed=embed)
                return await self.call_number(player, game)
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="Ooops! Time's up :slight_frown:",
                description=f"You took too long to call a number. You turn is skipped.",
                color=0xBEBEFE,
            )
            await player.send(embed=embed)
            return False

    
    def create_bingo_chart(self):
        numbers = list(range(1, 26))
        random.shuffle(numbers)
        return [numbers[i:i + 5] for i in range(0, 25, 5)]
    
    def is_number_valid(self, number, game):
        if number in game["called_numbers"]:
            return False
        # Check if number is in the current player's chart
        for row in game["chart"][game["current_player"].id]:
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
        chart_display = str()
        for i, row in enumerate(chart):
            chart_display += "||"
            for j, cell in enumerate(row):
                if cell > 0:
                    chart_display += f" {cell:2} "
                elif cell < 0:
                    chart_display += f"  X "
                chart_display += " " if j < 4 else "||"
            chart_display += "\n" if i < 4 else ""
        return f"```\n{chart_display}```"
    
    def get_scores_message(self, game):
        message = str()
        max_score = max(game["score"].values())
        for player in game["players"]:
            score = game["score"][player.id]
            message += f'{player .mention}: ({score}) :\t'
            message += " ".join([f"***~~{letter}~~***" if i < score else f"**{letter}**" for i, letter in enumerate('BINGO')])
            if score == max_score:
                message += "\t:crown:"
            message += "\n"
        return message
    
async def setup(bot):
    await bot.add_cog(Bingo(bot))