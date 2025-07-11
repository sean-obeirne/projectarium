#!/usr/bin/env python3

#
# Author: Sean O'Beirne
# Date: 12-18-2024
# File: projectarium
# Usage: projectarium
#

#
# Kanban board TUI built with Python curses
#


import curses
import sqlite3
import os
import sys
from typing import Required


import logging
logging.basicConfig(filename='debug.log', level=logging.DEBUG, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')
os.system("touch debug.log")  # Create the log file if it doesn't exist

from config import *

# custom curses color module
from ccolors import *       # pyright: ignore[reportWildcardImportFromLibrary]
from cinput import *       # pyright: ignore[reportWildcardImportFromLibrary]

import state
import db
from ui.layout import *



# Configure curses
stdscr = curses.initscr()
curses.start_color()
curses.use_default_colors()
init_16_colors()

SCREEN_HEIGHT, SCREEN_WIDTH = stdscr.getmaxyx()
SECTION_HEIGHT          = (SCREEN_HEIGHT - COMMAND_WINDOW_HEIGHT)
SECTION_WIDTH           = (SCREEN_WIDTH - (3 * X_PAD)) // 4 # right-hand padding


def init():
    stdscr.clear()

    curses.curs_set(0)
    curses.noecho()
    curses.set_escdelay(1)
    stdscr.keypad(True)

    stdscr.refresh()


    # Connect to database (or create it if it doesn't exist)
    if sys.argv[0][-3:] == ".py":
        conn = sqlite3.connect(DB_PATH)
    else:
        conn = sqlite3.connect(PROD_DB_PATH)
        # conn = sqlite3.connect(DB_PATH)

    cw = CommandWindow()
        
    dm = db.DatabaseManager(conn)
    dm.init()
    log.info("Database initialized")

    windows = [Window(i, curses.newwin(SECTION_HEIGHT, SECTION_WIDTH, 0, ((i) * SECTION_WIDTH) + (i * X_PAD)), list(STATUSES.keys())[i], color=STATUSES[list(STATUSES.keys())[i]][1]) for i in range(4)]

    sm = state.StateManager(dm, cw)
    sm.init(windows)
    log.info("State initialized")

    return sm


def main(stdscr):
    sm = init()
    sm.update_windows()

    todo_keymap = {
        "q":        lambda:   sm.quit_todo(),
        "a":        lambda:   sm.add_item(),
        "KEY_UP":   lambda:   sm.tm.up(),       # pyright: ignore[reportOptionalMemberAccess]
        "KEY_DOWN": lambda:   sm.tm.down(),     # pyright: ignore[reportOptionalMemberAccess]
        "d":        lambda:   sm.delete_item(),
        "e":        lambda:   sm.edit_item(),
        "h":        lambda:   sm.left(),
        "l":        lambda:   sm.right(),
        "k":        lambda:   sm.up(),
        "j":        lambda:   sm.down(),
    }


    keymap = {
        "q":    lambda: exit(0),
        "\x1b": lambda: exit(0),

        "a": lambda:  sm.add_project(),
        "d": lambda:  sm.delete_project(),
        "e": lambda:  sm.edit_project(),

        "c": lambda:  sm.open_dir(),
        "C": lambda:  sm.open_dir(True),
        "n": lambda:  sm.open_nvim(),
        "N": lambda:  sm.open_nvim(True),
        "b": lambda:  sm.open_both(),
        "B": lambda:  sm.open_both(True),
        "x": lambda:  sm.open_tmux(),
        "X": lambda:  sm.open_tmux(True),
        "t": lambda:  sm.open_todo(),
        "p": lambda:  sm.progress(),
        "r": lambda:  sm.regress(),
        "+": lambda:  sm.increment_priority(),
        "-": lambda:  sm.decrement_priority(),

        "KEY_LEFT":   lambda:  sm.left(),
        "KEY_RIGHT":  lambda:  sm.right(),
        "KEY_UP":     lambda:  sm.up(),
        "KEY_DOWN":   lambda:  sm.down(),

        "m": lambda:  sm.next_mode(),
    }

    # Main loop
    while True:
        # get and handle input
        key = stdscr.getkey()
        if sm.in_todo:
            if key not in todo_keymap: continue
            todo_keymap[key]()
        else: 
            if key not in keymap: continue
            keymap[key]()


if __name__ == "__main__":
    curses.wrapper(main)

