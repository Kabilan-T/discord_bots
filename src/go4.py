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

class Go4Bot(BaseBot):
    ''' Go-4 bot class definition '''

    def __init__(self):
        ''' Initialize the bot '''
        super().__init__('go4')
    
if __name__ == '__main__':
    # Launch the bot
    TOKEN = os.getenv('GO4_BOT_TOKEN', None)
    mo_bot = Go4Bot()
    mo_bot.run(TOKEN)