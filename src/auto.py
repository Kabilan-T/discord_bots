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
        config_file = 'auto.yml'
        self.default_color = discord.Color.purple()
        self.extensions_to_load =  ['cogs.general', 
                                    'cogs.auto.moderation',
                                    'cogs.auto.greetings',
                                    'cogs.auto.roles']
        super().__init__(config_file, self.default_color, self.extensions_to_load)
    
if __name__ == '__main__':
    # Launch the bot
    TOKEN = os.getenv('AUTO_BOT_TOKEN', None)
    auto_bot = AutoBot()
    auto_bot.run(TOKEN)
