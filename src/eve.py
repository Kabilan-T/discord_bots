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
        super().__init__('eve')
    
if __name__ == '__main__':
    # Launch the bot
    TOKEN = os.getenv('EVE_BOT_TOKEN', None)
    eve_bot = EveBot()
    eve_bot.run(TOKEN)