#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' MO bot execution script '''

#-------------------------------------------------------------------------------

import os
import discord
from bots.base import BaseBot

class MoBot(BaseBot):
    ''' Mo bot class definition '''

    def __init__(self):
        ''' Initialize the bot '''
        bot_name = 'mo'
        self.default_color = discord.Color.purple()
        self.extensions_to_load  = ['cogs.general',
                                    'cogs.mo.instagram']
        super().__init__(bot_name, self.default_color, self.extensions_to_load)
    
if __name__ == '__main__':
    # Launch the bot
    TOKEN = os.getenv('MO_BOT_TOKEN', None)
    mo_bot = MoBot()
    mo_bot.run(TOKEN)