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

    
HEADER = [
r"""Projectarium"""
        ]

FOOTER = [
r"""*help placeholder*"""
        ]

TERMINAL_PREFIX = "gnome-terminal --maximize --working-directory="
NEOVIM_PREFIX = "nvim "
actions = {}


BACKLOG = 0
BLOCKED = 1
ACTIVE = 2
DONE = 3

class Button:

    def __init__(self, y, x, key, name, path="", command="", sctype="gt"):
        self.y = y
        self.x = x
        self.key = key
        self.name = name
        self.path = path
        self.sctype = sctype
        if sctype == "gt":
            self.command = f"{TERMINAL_PREFIX}{path}"
            if command == "nvim":
                self.command += f" -- {command} {path}"
        elif sctype == "app":
            self.command = command
        elif sctype == "internal":
            self.command = command
        # log.info(f"Command created: {self.command}")
        actions[self.key] = self.command

    def draw(self):
        x = self.x
        swap_exists = self.swap_exists()
        # dir_open = self.dir_open()
        is_open = swap_exists #or dir_open
        is_open = False
        is_open = is_open and self.name != 'Terminal'

        # prefix
        if is_open:
            stdscr.addch(self.y, x-3, '▪', DARK_GREY)
        else:
            stdscr.addch(self.y, x-3, '▪', WHITE)
        stdscr.addch(self.y, x, '[', CYAN)
        x += 1

        # orange/black number for open files
        if is_open:
            stdscr.addch(self.y, x, self.key, BLACK)
        else:
            stdscr.addch(self.y, x, self.key, ORANGE)
        x += 1

        # suffix
        stdscr.addch(self.y, x, ']', CYAN)
        x += 1
        if is_open:
            stdscr.addstr(self.y, x, f" {self.name}", DARK_GREY)
        else:
            stdscr.addstr(self.y, x, f" {self.name}", WHITE)

    def build_command(self):
        return self.command + " " + self.path

    def swap_exists(self):
        swaps = os.listdir("/home/sean/.config/nvim/swap") + os.listdir("/home/sean/.local/state/nvim/swap")
        for sf in swaps:
            if sf.replace("%", "/")[0:-4] == self.path:
                return True
        return False

    def dir_open(self):
        if self.command[0:14] == "gnome-terminal":
            fish_pids = subprocess.check_output(['pgrep', 'fish'], text=True).split('\n')
            log.info(fish_pids)
            for pid in fish_pids:
                cmd = f"lsof -p {pid} | head -n 2 | tail -n 1"
                out = subprocess.check_output(cmd, shell=True, text=True).split()
                log.info(out)
                if out[0] == 'fish':
                    return f"{out[-1]}/" == self.path
        return False

class Window:
    def __init__(self, height, width, y, x, title="", color=WHITE, style=NORMAL):
        self.h = height
        self.w = width
        self.y = y
        self.x = x
        self.win = curses.newwin(self.h, self.w, self.y, self.x)
        self.title = title
        self.color = color
        self.style = style
        self.cards = []
        self.new_card_y = 2

    def draw(self):
        self.win.attron(self.color | self.style)
        self.win.box()
        self.win.addstr(0, 2, f" {self.title} " if self.title != "" else "")
        self.win.attroff(self.color | self.style)
        for card in self.cards:
            card.draw()

    def refresh(self):
        self.win.refresh()
        for card in self.cards:
            card.refresh()

    def add_card(self, project_name, path, file=""):
        self.cards.append(Card(3, self.w - 4, self.new_card_y, self.x + 2, project_name, path, file))
        self.new_card_y += 3
        self.draw()
        self.refresh()

    def get_card(self, index):
        return self.cards[index]

    def card_count(self):
        return len(self.cards)

    def delete_card(self, card):
        self.cards.remove(card)
        self.draw()
        self.refresh()


class Card():
    def __init__(self, h, w, y, x, project_name, path, file=""):
        self.h, self.w = h, w
        self.y, self.x = y, x
        self.win = curses.newwin(self.h, self.w, self.y, self.x)
        self.project_name = project_name
        self.path = path
        self.file = file
        self.active = False
        self.color = WHITE

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
        self.win.attron(self.color | BOLD)
        self.win.box()
        self.win.addstr(1, 2, self.project_name)
        self.win.attroff(self.color | BOLD)

    def refresh(self):
        self.win.refresh()

    def activate(self):
        self.h = 6
        self.active = True
        self.color = ORANGE
        self.draw()
        self.refresh()

    def deactivate(self):
        self.active = False
        self.color = WHITE
        self.draw()
        self.refresh()

def open_todo():
    pass


def make_title():
    pass

def draw_ascii(x, y, image, map, bold_color=-1):
    i = 0
    cx = x
    cy = y
    for line in image:
        for char in line:
            this = int(map[i], 16)
            stdscr.addch(cy, cx, char, curses.color_pair(this) | (curses.A_BOLD if this == bold_color else 0))
            i += 1
            cx += 1
        cy += 1
        cx = x


def draw():
    # Clear screen
    stdscr.clear()

    # Turn off cursor blinking and echoing
    curses.curs_set(0)
    curses.noecho()
    curses.set_escdelay(1)

    # Get screen height and width
    height, width = stdscr.getmaxyx()

    win_height, win_width = 10, 40
    win_y, win_x = (height - win_height) // 2, (width - win_width) // 2  # Center the window

    win = curses.newwin(win_height, win_width, win_y, win_x)

    # Add a border to the window
    win.box()

    win.refresh()
    stdscr.refresh()


    # stdscr.addstr(11, 6, "NeoVim Shortcuts:", WHITE)
    # stdscr.addstr(11, 6 + 40, "Directory Shortcuts:", WHITE)
    # stdscr.addstr(25, 6, "Application Shortcuts:", WHITE)


def main(stdscr):
    draw()

    stdscr.keypad(True)
    height, width = stdscr.getmaxyx()
    x, y = 0, 0

    buttons = []


    section_width = (width - 8) // 4
    # buttons.append(Button(height-2, 8, 'q', 'Quit', command='exit'))
    # buttons.append(Button(height-3, 8, 'e', 'Edit', command='nvim', path='/home/sean/code/in-progress/landing-page/landing-page.py'))
    screen = Window(height - 0, width, 0, 0, "", color=WHITE, style=NORMAL)
    x += 2
    backlog = Window(height - 2, section_width, 1, x, "Backlog", color=BLUE, style=BOLD)
    x += 2 + backlog.w
    blocked = Window(height - 2, section_width, 1, x, "Blocked", color=RED, style=BOLD)
    x += 2 + blocked.w
    active = Window(height - 2, section_width, 1, x, "Active", color=YELLOW, style=BOLD)
    x += 2 + active.w
    done = Window(height - 2, section_width, 1, x, "Done", color=GREEN, style=BOLD)
    x += 2 + done.w
    backlog.add_card("ROMs", "/home/sean/code/future/ROMs/")
    blocked.add_card("WotR", "/home/sean/code/paused/godot/Wizards-of-the-Rift/")
    blocked.add_card("LearnScape", "/home/sean/code/paused/LearnScape/")
    active.add_card("goverse", "/home/sean/code/active/go/goverse/")
    active.add_card("projectarium", "/home/sean/code/active/python/projectarium/", "projectarium.py")
    active.add_card("snr", "/home/sean/.config/nvim/lua/snr/", "init.lua")
    active.add_card("macro-blues", "/home/sean/code/active/c/macro-blues/", "macro-blues/")
    active.add_card("leetcode", "/home/sean/code/paused/leetcode/")
    active.add_card("TestTaker", "/home/sean/code/paused/TestTaker/")
    done.add_card("Sorter", "/home/sean/code/done/Sorter/", "sorter.py")
    done.add_card("landing-page", "/home/sean/code/done/landing-page/", "landing-page.py")
    windows = [backlog, blocked, active, done]
    active_window = BACKLOG
    active_row = 0


    screen.draw()
    screen.refresh()
    for window in windows:
        window.draw()
        window.refresh()
    windows[active_window].get_card(active_row).activate()


    valid_keys = {
            'c',
            'n',
            't',
            'r',
            'p',
            'a',
            ' ',
            '\x1b'
            }

    # Main loop
    while True:
        # get and handle input
        for button in buttons:
            button.draw()
        og_row, og_window = active_row, active_window
        key = stdscr.getkey()
        if key == 'q' or key == '\x1b':
            log.info("Quitting...")
            exit(0)
        if key == ' ':
            continue
        if key == 'a':
            windows[active_window].add_card("another", "/some/path")
            continue
        if key == "KEY_DOWN":
            active_row += 1
            if active_row >= windows[active_window].card_count():
                active_row = windows[active_window].card_count() - 1
            if active_row != og_row:
                windows[og_window].get_card(og_row).deactivate()
            windows[active_window].get_card(active_row).activate()
        if key == "KEY_UP":
            active_row -= 1
            if active_row < 0:
                active_row = 0
            if active_row != og_row:
                windows[og_window].get_card(og_row).deactivate()
            windows[active_window].get_card(active_row).activate()
        if key == "KEY_RIGHT":
            active_window += 1
            if active_window > 3:
                active_window = 3
            active_row = min(active_row, windows[active_window].card_count() - 1)
            if active_window != og_window:
                windows[og_window].get_card(og_row).deactivate()
            windows[active_window].get_card(active_row).activate()
        if key == "KEY_LEFT":
            active_window -= 1
            if active_window < 0:
                active_window = 0
            active_row = min(active_row, windows[active_window].card_count() - 1)
            if active_window != og_window:
                windows[og_window].get_card(og_row).deactivate()
            windows[active_window].get_card(active_row).activate()

        if key == 'c':
            os.system(TERMINAL_PREFIX + windows[active_window].get_card(active_row).path)
            continue
        if key == 'n':
            os.system(NEOVIM_PREFIX + windows[active_window].get_card(active_row).path + windows[active_window].get_card(active_row).file)
            continue
        if key == 't':
            # open_todo(windows[active_window].get_card(active_row).project_name)
            continue
        if key == 'p':
            temp_card = windows[active_window].get_card(active_row)
            windows[active_window].delete_card(temp_card)
            windows[active_window + 1].add_card(temp_card.project_name, temp_card.path)
            continue
        if key == 'r':
            temp_card = windows[active_window].get_card(active_row)
            windows[active_window].delete_card(temp_card)
            windows[active_window - 1].add_card(temp_card.project_name, temp_card.path)
            continue
        if key in valid_keys:
            log.info(f"'{key}' action: {actions[key].split()}")
            if key == key.lower():
                if key == 'r':
                    os.system("/home/sean/applications/RuneLite.AppImage --scale 2 > /tmp/runelite.log")
                else:
                    subprocess.run(actions[key].split())
            else:
                exec(actions[key])
            draw()
            stdscr.refresh()
        else:
            log.error(f"Invalid key {key}")


        # update the screen
        stdscr.refresh()

if __name__ == "__main__":
    curses.wrapper(main)

