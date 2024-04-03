#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' AUTO bot execution script '''

#-------------------------------------------------------------------------------

import os
import discord
from bots.base import BaseBot

class AutoBot(BaseBot):
    ''' Auto bot class definition '''

    def __init__(self):
        ''' Initialize the bot '''
        super().__init__('auto')
    
if __name__ == '__main__':
    # Launch the bot
    TOKEN = os.getenv('AUTO_BOT_TOKEN', None)
    auto_bot = AutoBot()
    auto_bot.run(TOKEN)
