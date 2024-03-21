#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' EVE bot execution script '''

#-------------------------------------------------------------------------------

import os
import discord
from bots.base import BaseBot

class EveBot(BaseBot):
    ''' Eve bot class definition '''

    def __init__(self):
        ''' Initialize the bot '''
        config_file = 'eve.yml'
        self.default_color = discord.Color.purple()
        self.voice = {'default_volume': 75, 'language': 'ta'}
        self.extensions_to_load =  ['cogs.general',
                                    'cogs.eve.bingo',
                                    'cogs.eve.voice']
        super().__init__(config_file, self.default_color, self.extensions_to_load)
    
if __name__ == '__main__':
    # Launch the bot
    TOKEN = os.getenv('EVE_BOT_TOKEN', None)
    eve_bot = EveBot()
    eve_bot.run(TOKEN)