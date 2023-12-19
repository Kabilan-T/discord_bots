#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kabilan Tamilmani
# E-mail: kavikabilan37@gmail.com
# Github: Kabilan-T

''' Main file for the project'''

#-------------------------------------------------------------------------------

from src.bot import MyBot

if __name__ == '__main__':
    # Launch the bot
    bot = MyBot()
    bot.run()