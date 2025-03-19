#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Command related to chatting with the bot '''

#-------------------------------------------------------------------------------

import os
from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer
import discord
from discord.ext import commands
from discord.ext.commands import Context

class Chatter(commands.Cog, name="Chatting Features"):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = os.path.join(self.bot.data_dir, 'database.db')
        # Create a ChatBot instance
        self.chatbot = ChatBot('M-O_Bot',
                storage_adapter='chatterbot.storage.SQLStorageAdapter',
                logic_adapters=[
                    'chatterbot.logic.BestMatch',
                    'chatterbot.logic.MathematicalEvaluation'
                ],
                database_uri=f'sqlite:///{self.db_path}')
        if not os.path.exists(self.db_path):
            self.train_chatbot()
        self.open_conversations = dict()
    
    def train_chatbot(self):
        ''' Train the chatbot '''
        trainer = ChatterBotCorpusTrainer(self.chatbot)
        trainer.train('chatterbot.corpus.english')
        trainer.train("chatterbot.corpus.english.greetings")
        trainer.train("chatterbot.corpus.english.conversations")
        trainer.train("chatterbot.corpus.english.emotion")

    @commands.command(name='chat', description='Open a conversation with bot', aliases=['c'])
    async def chat(self, context: Context):
        ''' Chat with the bot '''
        channel = context.channel
        author = context.author
        if channel in self.open_conversations.keys():
            self.open_conversations[channel].append(author)
        else:
            self.open_conversations[channel] = [author]
        embed = discord.Embed(
            title='Let\'s Chat! :speech_balloon:',
            description="Hello! I have opened a chat session with you in this channel",
            color=self.bot.default_color,
        )
        embed.add_field(name="I respond as I wish :wink:", value="I'm not always accurate/meaningful \n *My way or the highway!* :nail_care:", inline=False)
        embed.set_footer(text=f"Type 'end' or use the command `{self.bot.prefix[context.guild.id]}end` to end the chat session.")
        await context.reply(embed=embed)
        self.bot.log.info(f'Started chat session with {author.name} in {channel.name}', guild=context.guild)
    
    @commands.command(name='end', description='End the chat session', aliases=['e'])
    async def end(self, context: Context):
        ''' End the chat session '''
        channel = context.channel
        author = context.author
        if channel in self.open_conversations.keys():
            if author in self.open_conversations[channel]:
                self.open_conversations[channel].remove(author)
                if len(self.open_conversations[channel]) == 0:
                    del self.open_conversations[channel]
                embed = discord.Embed(
                    title='Closing Chat :wave:',
                    description='The chat session has been ended.',
                    color=self.bot.default_color,
                )
                await context.reply(embed=embed)
                self.bot.log.info(f'Ended chat session with {author.name} in {channel.name}', guild=context.guild)
            else:
                embed = discord.Embed(
                    title='Sorry! :confused:',
                    description='You do not have an active chat session in this channel.',
                    color=self.bot.default_color,
                )
                await context.reply(embed=embed)
                self.bot.log.warning(f'{author.name} tried to end a chat session without an active session in {channel.name}', guild=context.guild)
                return
        else:
            embed = discord.Embed(
                title='Sorry! :confused:',
                description='There is no active chat session in this channel.',
                color=self.bot.default_color,
            )
            await context.reply(embed=embed)
            self.bot.log.warning(f'{author.name} tried to end a chat session without an active session in {channel.name}', guild=context.guild)
            return
    
    @commands.command(name='train', description='Train the bot again')
    async def train(self, context: Context):
        ''' Train the bot again '''
        self.train_chatbot()
        embed = discord.Embed(
            title='Training Complete! :white_check_mark:',
            description='The bot has been trained again.',
            color=self.bot.default_color,
        )
        await context.reply(embed=embed)
        self.bot.log.info('Trained the bot again', guild=context.guild)

    @commands.Cog.listener()
    async def on_message(self, message):
        ''' Listen for messages '''
        if message.author == self.bot.user:
            return
        if message.content.startswith(self.bot.prefix[message.guild.id]):
            return
        if message.channel in self.open_conversations.keys():
            if message.author in self.open_conversations[message.channel]:
                if message.content.lower() == 'end':
                    self.open_conversations[message.channel].remove(message.author)
                    if len(self.open_conversations[message.channel]) == 0:
                        del self.open_conversations[message.channel]
                    embed = discord.Embed(
                        title='Closing Chat :wave:',
                        description='The chat session has been ended.',
                        color=self.bot.default_color,
                    )
                    await message.reply(embed=embed)
                    self.bot.log.info(f'Ended chat session with {message.author.name} in {message.channel.name}', guild=message.guild)
                else:
                    response = self.chatbot.get_response(message.content)
                    embed = discord.Embed(
                        description=response,
                        color=self.bot.default_color,
                    )
                    await message.reply(embed=embed)
                    self.bot.log.info(f'Responded to {message.author.name} in {message.channel.name}', guild=message.guild)

async def setup(bot):
    await bot.add_cog(Chatter(bot))