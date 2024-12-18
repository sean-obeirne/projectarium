#!/usr/bin/env python3

#
# Author: Sean O'Beirne
# Date: 7-29-2024
# File: landing-page.py
# Usage: python3 landing-page
#

#
# Boilerplate for curses application
#


import curses
from curses.textpad import rectangle

import random

import subprocess, os, sys

import time

import logging

import sqlite3

# Configure logging
logging.basicConfig(filename='debug.log', level=logging.DEBUG, filemode='w',
                    format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

stdscr = curses.initscr()


curses.start_color()
curses.use_default_colors()

# Define colors
def hex_to_rgb(hexstring):
    r = int(int(hexstring[0:2], 16) * 1000 / 255)
    g = int(int(hexstring[2:4], 16) * 1000 / 255)
    b = int(int(hexstring[4:6], 16) * 1000 / 255)
    return (r, g, b)

green = hex_to_rgb("29ad2b")
brown = hex_to_rgb("896018")
white = hex_to_rgb("ffffff")

tn_bg = hex_to_rgb("24283b")
tn_bg_dark = hex_to_rgb("1f2335")
tn_bg_highlight = hex_to_rgb("292e42")
tn_blue = hex_to_rgb("7aa2f7")
tn_blue0 = hex_to_rgb("3d59a1")
tn_blue1 = hex_to_rgb("2ac3de")
tn_blue2 = hex_to_rgb("0db9d7")
tn_blue5 = hex_to_rgb("89ddff")
tn_blue6 = hex_to_rgb("b4f9f8")
tn_blue7 = hex_to_rgb("394b70")
tn_comment = hex_to_rgb("565f89")
tn_cyan = hex_to_rgb("7dcfff")
tn_dark3 = hex_to_rgb("545c7e")
tn_dark5 = hex_to_rgb("737aa2")
tn_fg = hex_to_rgb("c0caf5")
tn_fg_dark = hex_to_rgb("a9b1d6")
tn_fg_gutter = hex_to_rgb("3b4261")
tn_green = hex_to_rgb("9ece6a")
tn_green1 = hex_to_rgb("73daca")
tn_green2 = hex_to_rgb("41a6b5")
tn_magenta = hex_to_rgb("bb9af7")
tn_magenta2 = hex_to_rgb("ff007c")
tn_orange = hex_to_rgb("ff9e64")
tn_purple = hex_to_rgb("9d7cd8")
tn_red = hex_to_rgb("f7768e")
tn_red1 = hex_to_rgb("db4b4b")
tn_teal = hex_to_rgb("1abc9c")
tn_terminal_black = hex_to_rgb("414868")
tn_yellow = hex_to_rgb("e0af68")
tn_git_add = hex_to_rgb("449dab")
tn_git_change = hex_to_rgb("6183bb")
tn_git_delete = hex_to_rgb("914c54")



COLOR_BLACK = 0
COLOR_RED = 1
COLOR_GREEN = 2
COLOR_ORANGE = 3
COLOR_BLUE = 4
COLOR_MAGENTA = 5
COLOR_CYAN = 6
COLOR_WHITE = 7
COLOR_DARK_GREY = 8
COLOR_LIGHT_RED = 9
COLOR_LIGHT_GREEN = 10
COLOR_YELLOW = 11
COLOR_LIGHT_BLUE = 12
COLOR_PURPLE = 13
COLOR_BROWN = 14
COLOR_DIM_WHITE = 15

# RGB values (0-1000 scale)
color_definitions = {
    COLOR_BLACK: tn_terminal_black,
    COLOR_RED: tn_red1,
    COLOR_GREEN: green,
    COLOR_ORANGE: tn_orange,
    COLOR_BLUE: tn_blue0,
    COLOR_MAGENTA: tn_magenta2,
    COLOR_CYAN: tn_cyan,
    COLOR_WHITE: white,
    COLOR_DARK_GREY: tn_dark5,
    COLOR_LIGHT_RED: tn_red,
    COLOR_LIGHT_GREEN: tn_green,
    COLOR_YELLOW: tn_yellow,
    COLOR_LIGHT_BLUE: tn_blue,
    COLOR_PURPLE: tn_purple,
    COLOR_BROWN: brown,
    COLOR_DIM_WHITE: tn_fg,
}



# Initialize 16 colors
def init_16_colors():
    curses.start_color()
    
    if curses.can_change_color():
        for color, rgb in color_definitions.items():
            curses.init_color(color, *rgb)
    
    # Define color pairs using custom color numbers
    curses.init_pair(1, COLOR_BLACK, -1)
    curses.init_pair(2, COLOR_RED, -1)
    curses.init_pair(3, COLOR_GREEN, -1)
    curses.init_pair(4, COLOR_ORANGE, -1)
    curses.init_pair(5, COLOR_BLUE, -1)
    curses.init_pair(6, COLOR_MAGENTA, -1)
    curses.init_pair(7, COLOR_CYAN, -1)
    curses.init_pair(8, COLOR_WHITE, -1)
    curses.init_pair(9, COLOR_DARK_GREY, -1)
    curses.init_pair(10, COLOR_LIGHT_RED, -1)
    curses.init_pair(11, COLOR_LIGHT_GREEN, -1)
    curses.init_pair(12, COLOR_YELLOW, -1)
    curses.init_pair(13, COLOR_LIGHT_BLUE, -1)
    curses.init_pair(14, COLOR_PURPLE, -1)
    curses.init_pair(15, COLOR_BROWN, -1)
    curses.init_pair(16, COLOR_DIM_WHITE, -1)

init_16_colors()

BLACK = curses.color_pair(1)
RED = curses.color_pair(2)
GREEN = curses.color_pair(3)
ORANGE = curses.color_pair(4)
BLUE = curses.color_pair(5)
MAGENTA = curses.color_pair(6)
CYAN = curses.color_pair(7)
WHITE = curses.color_pair(8)
DARK_GREY = curses.color_pair(9)
LIGHT_RED = curses.color_pair(10)
LIGHT_GREEN = curses.color_pair(11)
YELLOW = curses.color_pair(12)
LIGHT_BLUE = curses.color_pair(13)
PURPLE = curses.color_pair(14)
BROWN = curses.color_pair(15)
DIM_WHITE = curses.color_pair(16)

NORMAL = curses.A_NORMAL
BOLD = curses.A_BOLD
ITALIC = curses.A_ITALIC

    
HEADER = "Projectarium"

FOOTER = [
r"""*help placeholder*"""
        ]

TERMINAL_PREFIX = "gnome-terminal --maximize --working-directory="
NEOVIM_PREFIX = "nvim "
actions = {}

DB_PATH = "projectarium.db"

FRAME = 0
BACKLOG = 1
BLOCKED = 2
ACTIVE = 3
DONE = 4

statuses = {
    BACKLOG: (BLUE, "Backlog"),
    BLOCKED: (RED, "Blocked"),
    ACTIVE: (YELLOW, "Active"),
    DONE: (GREEN, "Done"),
}
windows = []

active_card = -1
active_window = 0
def increment_active_card():
    global active_card
    a_win = windows[active_window]
    if active_card < len(a_win.cards) - 1:
        a_win.cards[active_card].deactivate()
        active_card += 1
        a_win.cards[active_card].activate()
        a_win.draw()
        a_win.refresh()

def decrement_active_card():
    global active_card
    if active_card > 0:
        windows[active_window].cards[active_card].deactivate()
        windows[active_window].cards[active_card].shove(True)
        active_card -= 1
        windows[active_window].cards[active_card].activate()
        windows[active_window].draw()
        windows[active_window].refresh()

# def increment_active_window():
#     global active_window
#     active_window += 1
# def decrement_active_window():
#     global active_window
#     active_window -= 1


# def add_card(name, path, file=""):
    # cards.append(Card(name, path, file))

class Window:
    def __init__(self, id, height, width, y, x, conn, title, title_pos=2, color=WHITE, style=NORMAL):
        self.id = id
        self.h = height
        self.w = width
        self.y = y
        self.x = x
        self.win = curses.newwin(self.h, self.w, self.y, self.x)
        self.conn = conn
        self.cursor = self.conn.cursor()
        self.title = title
        self.color = color
        self.style = style
        self.title_pos = title_pos
        self.cards = []
        self.card_offset = 0
        self.last_active = active_card

    def pull(self):
        self.cursor.execute("SELECT * FROM projects WHERE status = ? ORDER BY LOWER(name);", (self.title,))
        rows = self.cursor.fetchall()
        for row in rows:
            self.cards.append(Card(3, self.w, self.y + self.card_offset, self.x + 2, row[1], row[3], row[5]))
            self.card_offset += 3

    def contains(self, name):
        # for card in self.cards:
        # if name in lambda x: self.cards[x].name:
            # print("fail")
        pass

    def draw_cards(self):
        shove = False
        for card in self.cards:
            card.win.erase()
            if card.active:
                card.height = 6
                card.active = True
                card.color = ORANGE
                card.unshove()
                shove = True # aka found active
            else:
                card.height = 3
                card.active = False
                card.color = WHITE
                if shove:
                    card.shove()
                    card.is_shoved = True
                # else:
                #     card.scrunch()
                #     card.is_scrunched = True
            card.win.resize(card.height, card.width - 4)

            card.win.attron(card.color | BOLD)
            card.win.box()
            card.win.addstr(1, 2, card.name)
            card.win.attroff(card.color | BOLD)

            card.refresh()

    def draw(self):
        self.win.attron(self.color | self.style)
        self.win.box()
        self.win.addstr(0, self.title_pos, f" {self.title} " if self.title != "" else "")
        self.win.attroff(self.color | self.style)
        self.win.refresh()

        self.draw_cards()

    def refresh(self):
        self.win.refresh()


class Card():
    def __init__(self, height, width, y, x, name, path, file=""):
        self.height = height
        self.width = width
        self.y = y
        self.x = x
        self.win = curses.newwin(self.height, self.width - 4, self.y + 1, self.x)
        self.name = name
        self.path = path
        self.file = file
        self.active = False
        self.color = WHITE
        self.is_shoved = False
        self.is_scrunched = False

    def draw_active(self):
        strings = ["    cd", "nvim", "      todo", "progress", "regress"]
        colors = [WHITE, WHITE, DIM_WHITE, DARK_GREY, DARK_GREY]
        y = 2
        x = 4
        for i, string in enumerate(strings):
            leading_spaces = len(string) - len(string.lstrip())
            self.win.addstr(y, x, " " * leading_spaces, colors[i])  # Add leading spaces
            x += leading_spaces


            self.win.addch(y, x, '[', CYAN)
            x += 1
            self.win.addch(y, x, string.lstrip()[0], colors[i])
            x += 1
            self.win.addch(y, x, ']', CYAN)
            x += 1
            self.win.addstr(y, x, string.lstrip()[1:], colors[i])
            x += len(string.lstrip()[1:]) + 2

            if string not in ("progress", "    cd"):
                y += 1
                x = 4

    def clear(self):
        self.win.erase()

    def draw(self):
        # if self.active:
            # self.draw_active()
        # else:
            # self.clear()
        pass

    def refresh(self):
        self.win.refresh()

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

    def shove(self, force=False):
        if not self.is_shoved or force:
            self.win.mvwin(self.y + 4, self.x)

    def unshove(self):
        if self.is_shoved:
            self.win.mvwin(self.y + 1, self.x)

    # def scrunch(self):
    #     if not self.is_scrunched:
    #         self.y -= 3
    #         self.win.mvwin(self.y + 1, self.x)

def open_todo():
    pass


def init():
    global active_card, active_window
    stdscr.keypad(True)

    height, width = stdscr.getmaxyx()
    x, y = 0, 0
    conn = sqlite3.connect(DB_PATH)

    windows.append(Window(FRAME, height, width, x, y, conn, HEADER, title_pos=width // 2 - len(HEADER) // 2 - 1, color=WHITE, style=NORMAL))

    section_width = (width - 8) // 4
    x += 2

    for i in range(len(statuses)):
        windows.append(Window(list(statuses.keys())[i], height - 2, section_width, 1, x, conn, statuses[i+1][1], color=statuses[i+1][0], style=BOLD))
        x += 2 + section_width

    # Connect to database (or create it if it doesn't exist)
    cursor = conn.cursor()

    # Create the 'projects' table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            path TEXT NOT NULL,
            file TEXT,
            status TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS todo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            priority TEXT,
            project_id,
            FOREIGN KEY (project_id) REFERENCES projects (id)
        )
    ''')

    # Optional: Insert some default data only if the database is empty
    cursor.execute("SELECT COUNT(*) FROM projects")
    if cursor.fetchone()[0] == 0:
        default_projects = [
            ("ROMs", "~/code/future/ROMs/", "Backlog"),
            ("WotR", "~/code/paused/godot/Wizards-of-the-Rift/", "Backlog"),
            ("LearnScape", "~/code/paused/LearnScape/", "Blocked"),
            ("goverse", "~/code/active/go/goverse/", "Active"),
            ("projectarium", "~/code/active/python/projectarium/", "Active"),
            ("snr", "/home/sean/.config/nvim/lua/snr/", "Backlog"),
            ("macro-blues", "/home/sean/code/active/c/macro-blues/", "Active"),
            ("leetcode", "/home/sean/code/paused/leetcode/", "Active"),
            ("TestTaker", "/home/sean/code/paused/TestTaker/", "Active"),
            ("Sorter", "~/code/done/Sorter/", "Done"),
            ("landing-page", "~/code/done/landing-page/", "Done"),
        ]
        cursor.executemany('''
            INSERT INTO projects (name, path, status)
            VALUES (?, ?, ?)
        ''', default_projects)

    # Commit changes and close connection
    conn.commit()
    # conn.close()

    win_set = False
    for window in windows:
        window.pull()
        if len(window.cards) > 0 and not win_set:
            win_set = True
            active_card = 0
            active_window = window.id
            window.cards[active_card].activate()
        



def draw():
    global active_card, active_window
    # Clear screen
    stdscr.clear()

    # Turn off cursor blinking and echoing
    curses.curs_set(0)
    curses.noecho()
    curses.set_escdelay(1)

    stdscr.refresh()

    for window in windows:
        if active_card == -1 and len(window.cards) > 0:
            active_card = 0
        if active_window == None:
            active_window = window,
        window.draw()
        window.refresh()
        # for card in window.cards:
            # card.draw()
            # card.refresh()


keymaps = {
    "q": lambda: exit(0),
    "\x1b": lambda: exit(0),

    "c": lambda: os.system(TERMINAL_PREFIX + ""),
    # "n": lambda: ,
    # "t": lambda: ,
    # "p": lambda: ,
    # "r": lambda: ,

    # "KEY_LEFT": lambda: ,
    # "KEY_RIGHT": lambda: ,
    "KEY_UP": lambda: decrement_active_card(),
    "KEY_DOWN": lambda: increment_active_card(),

    # "": lambda: ,
}

def main(stdscr):
    global active_card
    init()
    draw()

    # Main loop
    while True:
        # get and handle input
        key = stdscr.getkey()
        if key not in keymaps: continue
        keymaps[key]()

        # if key == 'a':
        #     add_card("another", "/some/path")
        #     continue
        # if key == "KEY_DOWN":
        #     active_row += 1
        #     if active_row >= windows[active_window].card_count():
        #         active_row = windows[active_window].card_count() - 1
        #     if active_row != og_row:
        #         windows[og_window].get_card(og_row).deactivate()
        #     windows[active_window].get_card(active_row).activate()
        # if key == "KEY_UP":
        #     active_row -= 1
        #     if active_row < 0:
        #         active_row = 0
        #     if active_row != og_row:
        #         windows[og_window].get_card(og_row).deactivate()
        #     windows[active_window].get_card(active_row).activate()
        # if key == "KEY_RIGHT":
        #     active_window += 1
        #     if active_window > 3:
        #         active_window = 3
        #     active_row = min(active_row, windows[active_window].card_count() - 1)
        #     if active_window != og_window:
        #         windows[og_window].get_card(og_row).deactivate()
        #     windows[active_window].get_card(active_row).activate()
        # if key == "KEY_LEFT":
        #     active_window -= 1
        #     if active_window < 0:
        #         active_window = 0
        #     active_row = min(active_row, windows[active_window].card_count() - 1)
        #     if active_window != og_window:
        #         windows[og_window].get_card(og_row).deactivate()
        #     windows[active_window].get_card(active_row).activate()

        if key == 'c':
            # os.system(TERMINAL_PREFIX + windows[active_window].get_card(active_card).path)
            continue
        if key == 'n':
            # os.system(NEOVIM_PREFIX + active_card.path + active_card.file)
            continue
        if key == 't':
            # open_todo(windows[active_window].get_card(active_row).project_name)
            continue
        if key == 'p':
            # temp_card = windows[active_window].get_card(active_row)
            # windows[active_window].delete_card(temp_card)
            # windows[active_window + 1].add_card(temp_card.project_name, temp_card.path)
            continue
        if key == 'r':
            # temp_card = windows[active_window].get_card(active_row)
            # windows[active_window].delete_card(temp_card)
            # windows[active_window - 1].add_card(temp_card.project_name, temp_card.path)
            continue
        # if key in valid_keys:
            # draw()
            # stdscr.refresh()
        else:
            log.error(f"Invalid key {key}")

if __name__ == "__main__":
    curses.wrapper(main)

