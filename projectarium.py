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
HELP = 5

statuses = {
    BACKLOG: (BLUE, "Backlog"),
    BLOCKED: (RED, "Blocked"),
    ACTIVE: (YELLOW, "Active"),
    DONE: (GREEN, "Done"),
}
windows = []

active_card: int = -1
active_window: int = 0
def increment_active_card():
    global active_card
    a_win = windows[active_window]
    if active_card < len(a_win.cards) - 1:
        a_win.cards[active_card].deactivate()
        active_card += 1
        a_win.cards[active_card].activate()
        a_win.draw()
        a_win.refresh()
        windows[HELP].draw_help()
        windows[HELP].refresh()

def decrement_active_card():
    global active_card
    a_win = windows[active_window]
    if active_card > 0:
        a_win.cards[active_card].deactivate()
        a_win.cards[active_card].shove(True)
        active_card -= 1
        a_win.cards[active_card].activate()
        a_win.draw()
        a_win.refresh()
        windows[HELP].draw_help()
        windows[HELP].refresh()

def increment_active_window():
    global active_window, active_card
    if active_window < len(windows) - 2:
        a_win = windows[active_window]
        if a_win.has_cards():
            a_win.cards[active_card].deactivate()
        a_win.scrunch()
        a_win.draw()
        a_win.refresh()
        active_window += 1
        n_a_win = windows[active_window]
        if len(n_a_win.cards) > 0:
            active_card = min(len(a_win.cards) - 1, len(n_a_win.cards) - 1, active_card) 
            if active_card == -1:
                active_card = 0
            n_a_win.cards[active_card].activate()
            for to_shove in n_a_win.cards[active_card+1:]:
                to_shove.shove(True)
        else:
            active_card = -1
            increment_active_window()
        n_a_win.draw()
        n_a_win.refresh()
        windows[HELP].draw_help()
        windows[HELP].refresh()
    
def decrement_active_window():
    global active_window, active_card
    if active_window > 1:
        a_win = windows[active_window]
        if a_win.has_cards():
            a_win.cards[active_card].deactivate()
            a_win.scrunch()
        a_win.draw()
        a_win.refresh()
        active_window -= 1
        n_a_win = windows[active_window]
        if len(n_a_win.cards) > 0:
            active_card = min(len(a_win.cards) - 1, len(n_a_win.cards) - 1, active_card) 
            if active_card == -1:
                active_card = 0
            if n_a_win.has_cards():
                n_a_win.cards[active_card].activate()
            for to_shove in n_a_win.cards[active_card+1:]:
                to_shove.shove(True)
            
        else:
            active_card = -1
            decrement_active_window() # TODOD: make this impossible
        n_a_win.draw()
        n_a_win.refresh()
        windows[HELP].draw_help()
        windows[HELP].refresh()


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

    def has_cards(self):
        return len(self.cards) > 0

    def pull(self):
        self.cursor.execute("SELECT * FROM projects WHERE status = ? ORDER BY LOWER(name);", (self.title,))
        rows = self.cursor.fetchall()
        self.cards.clear()
        self.card_offset = 0
        for row in rows:
            self.cards.append(Card(3, self.w, self.y + self.card_offset, self.x + 2, row[1], row[3], row[4], row[2]))
            self.card_offset += 3

    def contains(self, name):
        # for card in self.cards:
        # if name in lambda x: self.cards[x].name:
            # print("fail")
        pass

    def scrunch(self):
        for card in self.cards:
            card.unshove()

    def regress(self):
        global active_window
        if active_window <= 1:
            return
        self.cursor.execute('''
            UPDATE projects SET status = ? WHERE name = ?
        ''', (windows[active_window - 1].title, windows[active_window].cards[active_card].name))
        active_window -= 1
        progress_card_name = self.cards[active_card].name
        self.pull()
        windows[active_window].pull()
        self.conn.commit()
        self.draw()
        self.refresh()
        windows[active_window].activate_one(progress_card_name)
        windows[active_window].draw()
        windows[active_window].refresh()
        windows[HELP].draw_help()
        windows[HELP].refresh()

    def progress(self):
        global active_window
        if active_window >= 4:
            return
        self.cursor.execute('''
            UPDATE projects SET status = ? WHERE name = ?
        ''', (windows[active_window + 1].title, windows[active_window].cards[active_card].name))
        active_window += 1
        progress_card_name = self.cards[active_card].name
        self.pull()
        windows[active_window].pull()
        self.conn.commit()
        self.draw()
        self.refresh()
        windows[active_window].activate_one(progress_card_name)
        windows[active_window].draw()
        windows[active_window].refresh()
        windows[HELP].draw_help()
        windows[HELP].refresh()

    def activate_one(self, name):
        global active_card
        for i, card in enumerate(self.cards):
            card.deactivate()
            if card.name == name:
                active_card = i
                card.activate()
                self.draw()
                self.refresh()

    def draw_help(self):
        strings = ["cd", "nvim", "description", "todo", "progress", "regress"]
        y = 1
        x = 4
        for string in strings:
            self.win.addstr(y, x, f"{string[0]}: ", CYAN)
            x += 3
            if (active_window == 1 and string == "regress") \
                or (active_window == HELP-1 and string == "progress") \
                or (windows[active_window].cards[active_card].file in (None, "") and string == "nvim") \
                or (windows[active_window].cards[active_card].path == "" and string == "cd") \
                or (windows[active_window].cards[active_card].description in(None, "") and string == "description"):
                color = DARK_GREY
            else:
                color = WHITE
            self.win.addstr(y, x, f"{string}", color)
            x += len(string) + 5


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
            card.win.resize(card.height, card.width - 4)

            card.win.attron(card.color | BOLD)
            card.win.box()
            card.win.addstr(1, 2, card.name)
            card.win.attroff(card.color | BOLD)
            card.win.attron(WHITE)
            if card.active:
                card.win.addstr(2, 4, f"file: {card.file}") if card.file not in (None, "") else ""
            card.win.attroff(WHITE)

            card.refresh()

    def draw(self):
        self.win.attron(self.color | self.style)
        self.win.box()
        self.win.addstr(0, self.title_pos, f" {self.title}{" (" + str(len(self.cards)) + ") " if self.id not in (FRAME, HELP) else " "}" if self.title != "" else "")
        self.win.attroff(self.color | self.style)
        if self.id == HELP:
            self.draw_help()
        self.win.refresh()

        self.draw_cards()

    def refresh(self):
        self.win.refresh()


class Card():
    def __init__(self, height, width, y, x, name, path, file="", description=""):
        self.height = height
        self.width = width
        self.y = y
        self.x = x
        self.win = curses.newwin(self.height, self.width - 4, self.y + 1, self.x)
        self.name = name
        self.path = path
        self.file = file
        self.description = description
        self.active = False
        self.color = WHITE
        self.is_shoved = False
        self.is_scrunched = False

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




def open_todo():
    pass


def init():
    global active_card, active_window
    stdscr.keypad(True)

    height, width = stdscr.getmaxyx()
    x, y = 0, 0
    conn = sqlite3.connect(DB_PATH)

    windows.append(Window(FRAME, height - 3, width, y, x, conn, HEADER, title_pos=width // 2 - len(HEADER) // 2 - 1, color=WHITE, style=NORMAL))

    section_width = (width - 8) // 4
    x += 2

    for i in range(len(statuses)):
        windows.append(Window(list(statuses.keys())[i], height - 5, section_width, 1, x, conn, statuses[i+1][1], color=statuses[i+1][0], style=BOLD))
        x += 2 + section_width

    windows.append(Window(HELP, 3, width, height - 3, 0, conn, "Help", title_pos=width // 2 - len(HEADER) // 2 - 1, color=WHITE, style=NORMAL))

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
            ("ROMs",        "/home/sean/code/future/ROMs/",                     "",                 "Backlog"),
            ("WotR",        "/home/sean/code/paused/godot/Wizards-of-the-Rift/","",                 "Blocked"),
            ("LearnScape",  "/home/sean/code/paused/LearnScape/",               "learnscape.py",    "Blocked"),
            ("goverse",     "/home/sean/code/active/go/goverse/",               "cli/main.go",      "Active"),
            ("projectarium","/home/sean/code/active/python/projectarium/",      "projectarium.py",  "Active"),
            ("snr",         "/home/sean/.config/nvim/lua/snr/",                 "init.lua",         "Active"),
            ("macro-blues", "/home/sean/code/active/c/macro-blues/",            "macro-blues",      "Active"),
            ("leetcode",    "/home/sean/code/paused/leetcode/",                 "",                 "Active"),
            ("TestTaker",   "/home/sean/code/paused/TestTaker/",                "testtaker.py",      "Active"),
            ("Sorter",      "/home/sean/code/done/Sorter/",                     "sorter.py",        "Done"),
            ("landing-page","/home/sean/code/done/landing-page/",               "landing-page.py",  "Done"),
        ]
        cursor.executemany('''
            INSERT INTO projects (name, path, file, status)
            VALUES (?, ?, ?, ?)
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
        if active_card == -1 and len(window.cards) > 0 and active_window == 0:
            active_card = 0
            active_window = window.id,
        window.draw()
        window.refresh()


keymaps = {
    "q": lambda: exit(0),
    "\x1b": lambda: exit(0),

    " ": lambda: draw(),

    "c": lambda: os.system(TERMINAL_PREFIX + windows[active_window].cards[active_card].path),
    "n": lambda: os.system(TERMINAL_PREFIX + windows[active_window].cards[active_card].path + " -- bash -c \'" +  NEOVIM_PREFIX + windows[active_window].cards[active_card].file + "\'") if windows[active_window].cards[active_card].file != "" else "",
    # "t": lambda: ,
    "p": lambda: windows[active_window].progress(),
    "r": lambda: windows[active_window].regress(),

    "KEY_LEFT": lambda: decrement_active_window(),
    "KEY_RIGHT": lambda: increment_active_window(),
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
        if key == 't':
            # open_todo(windows[active_window].get_card(active_row).project_name)
            continue

if __name__ == "__main__":
    curses.wrapper(main)

