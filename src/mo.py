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
        super().__init__('mo')
    
if __name__ == '__main__':
    # Launch the bot
    TOKEN = os.getenv('MO_BOT_TOKEN', None)
    mo_bot = MoBot()
    mo_bot.run(TOKEN)