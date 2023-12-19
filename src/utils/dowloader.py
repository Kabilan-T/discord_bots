#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Media scraping commands for the bot'''

#-------------------------------------------------------------------------------

import discord
from discord.ext import commands
from discord.ext.commands import Context
import requests
from bs4 import BeautifulSoup

class Media(commands.Cog, name="Media"):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command( name="download", description="Download a file from a link.")
    async def download(self, context: Context, url: str):
        # Download a file from a link
        try:
            # Send a message indicating that the download is in progress
            await context.send(f'Downloading file from {url}...')

            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            media_url = None
            if soup.find('meta', property='og:image'):
                media_url = soup.find('meta', property='og:image')['content']
            elif soup.find('meta', property='og:video'):
                media_url = soup.find('meta', property='og:video')['content']

            if media_url:
                # Download the media file
                media_response = requests.get(media_url)
                with open('downloaded_media.jpg', 'wb') as file:
                    file.write(media_response.content)

                # Send the downloaded media file to the Discord channel
                await context.send(file=discord.File('downloaded_media.jpg'))
            else:
                await context.send('Unable to find media URL on the provided Instagram post.')

        except Exception as e:
            print(e)
            await context.send('An error occurred while processing the request.')


async def setup(bot):
    await bot.add_cog(Media(bot))