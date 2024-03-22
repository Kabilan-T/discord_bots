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
        bot_name = 'eve'
        self.default_color = 0xBEBEFE
        self.voice = {'default_volume': 75, 'language': 'ta', 'domain': 'co.in'}
        self.extensions_to_load =  ['cogs.general',
                                    'cogs.eve.bingo',
                                    'cogs.eve.voice']
        super().__init__(bot_name, self.default_color, self.extensions_to_load)
    
if __name__ == '__main__':
    # Launch the bot
    TOKEN = os.getenv('EVE_BOT_TOKEN', None)
    eve_bot = EveBot()
    eve_bot.run(TOKEN)