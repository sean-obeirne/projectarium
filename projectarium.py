#!/usr/bin/env python3

#
# Author: Sean O'Beirne
# Date: 12-18-2024
# File: projectarium
# Usage: projectarium
#

#
# Kanban board with Python curses
#


import curses
import sqlite3
import logging
import os
from enum import Enum, auto
import sys

import ccolors as c # custom color module



# Configure logging
logging.basicConfig(filename='debug.log', level=logging.DEBUG, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)


# Configure curses
stdscr = curses.initscr()
curses.start_color()
curses.use_default_colors()
c.init_16_colors()


#Configure windows
HEADER = "Projectarium"
FRAME = 0
ABANDONED = 0
BACKLOG = 1
ACTIVE = 2
DONE = 3
HELP = 4
STATUSES = {
    ABANDONED: ("Abandoned", c.RED),
    BACKLOG: ("Backlog", c.BLUE),
    ACTIVE: ("Active", c.BRIGHT_YELLOW),
    DONE: ("Done", c.GREEN),
}


# Assign other variables
PROD_DB_PATH = "/home/sean/bin/.projectarium.db"
DB_PATH = ".projectarium.db"
TERMINAL_PREFIX = "gnome-terminal --maximize --working-directory="
NEOVIM_PREFIX = "nvim "


# Screen layout dimensions
SCREEN_HEIGHT, SCREEN_WIDTH = stdscr.getmaxyx()
Y_PAD               = 1
X_PAD               = 2
HELP_HEIGHT         = 3
SECTION_HEIGHT      = (SCREEN_HEIGHT - HELP_HEIGHT - (2 * Y_PAD))
SECTION_WIDTH       = (SCREEN_WIDTH - (4 * X_PAD)) // 4 # right-hand padding
WINDOWS             = []
HELP_WINDOW         = None
INACTIVE_CARD_HEIGHT= 3
ACTIVE_CARD_HEIGHT  = 6
MODES = [BLAND := 0, COLORED := 1]
           
class StateManager:
    def __init__(self, dm,):
        self.dm = dm
        self.active_window = 0
        self.active_card = -1
        self.mode = BLAND

    def init(self):
        for window in WINDOWS:
            window.pull(self.dm)
            if self.active_card == -1 and len(window.cards) > 0:
                self.active_window = window.id
                self.active_card = 0
                WINDOWS[self.active_window].cards[self.active_card].activate()
                break
        self.update_windows()

    def update_windows(self): # TODO: only update active window and new active window
        for window in WINDOWS:
            window.update(self.dm, self.active_window, self.active_card)

    def update_window(self, window_id=None):
        window_id = self.active_window if window_id is None else window_id
        log.info("we are updating: " + str(window_id))
        WINDOWS[window_id].update(self.dm, window_id, self.active_card)


    def next_mode(self):
        self.mode = (self.mode + 1) % len(MODES)

    def up(self):
        if self.active_card > 0:
            self.active_card -= 1
            self.update_window()

    def down(self):
        if self.active_card < len(WINDOWS[self.active_window].cards) - 1:
            self.active_card += 1
            self.update_window()

    def right(self):
        if self.active_window < 3:
            self.active_window += 1
            self.active_card = min(self.active_card, len(WINDOWS[self.active_window].cards) - 1)
            self.update_windows()
            #TODO: get this to work
            # self.update_window()
            # self.update_window(self.active_window - 1)

    def left(self):
        if self.active_window > 0:
            self.active_window -= 1
            self.active_card = min(self.active_card, len(WINDOWS[self.active_window].cards) - 1)
            self.update_windows()


class DatabaseManager:
    def __init__(self, conn,):
        self.conn = conn
        self.cursor = conn.cursor()
        self.init()

    def init(self,):
        # Create the 'projects' table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT CHECK(LENGTH(description) <= 29),
                path TEXT NOT NULL,
                file TEXT,
                status TEXT NOT NULL,
                language TEXT
            )
        ''')
        # Create the 'todo' table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS todo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL UNIQUE,
                priority TEXT,
                deleted BOOLEAN NOT NULL DEFAULT 0,
                project_id,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        ''')

        self.conn.commit()

        if DB_PATH == ".projectarium.db":
            self.init_populate()

    def init_populate(self):
        if DB_PATH == ".projectarium.db":
            # Optional: Insert some default data only if the database is empty
            self.cursor.execute("SELECT COUNT(*) FROM projects")
            if self.cursor.fetchone()[0] == 0:
                default_projects = [
                    ("WotR",            "Wizards of the Rift",          "/home/sean/code/paused/godot/Wizards-of-the-Rift/","",                 "Abandoned",  "Godot"),
                    ("LearnScape",      "General learning visualizer",  "/home/sean/code/paused/LearnScape/",               "learnscape.py",    "Abandoned",  "Python"),
                    ("ROMs",            "ROM emulation optimization",   "/home/sean/code/future/ROMs/",                     "",                 "Backlog",      "C"),
                    ("goverse",         "Go VCS application",           "/home/sean/code/active/go/goverse/",               "cli/main.go",      "Active",       "Go"),
                    ("projectarium",    "Project progress tracker",     "/home/sean/code/active/python/projectarium/",      "projectarium.py",  "Active",       "Python"),
                    ("snr",             "Search and replace plugin",    "/home/sean/.config/nvim/lua/snr/",                 "init.lua",         "Active",       "Lua"),
                    ("todua",           "Todo list for Neovim",         "/home/sean/.config/nvim/lua/todua/",               "init.lua",         "Active",       "Lua"),
                    ("macro-blues",     "Custom macropad firmware",     "/home/sean/code/active/c/macro-c.BLUEs/",            "macro-c.BLUEs",      "Active",       "C"),
                    ("leetcode",        "Coding interview practice",    "/home/sean/code/paused/leetcode/",                 "",                 "Active",       "Python"),
                    ("TestTaker",       "ChatGPT->Python test maker",   "/home/sean/code/paused/TestTaker/",                "testtaker.py",     "Active",       "Python"),
                    ("Mission-Uplink",  "TFG Mission Uplink",           "/home/sean/code/tfg/Mission-Uplink/",              "README.md",        "Active",       "Go,C"),
                    ("Sorter",          "Sorting algoithm visualizer",  "/home/sean/code/done/Sorter/",                     "sorter.py",        "Done",         "Python"),
                    ("landing-page",    "Cute application launcher",    "/home/sean/code/done/landing-page/",               "landing-page.py",  "Done",         "Python"),
                    ################"   valid description length  "################################################################################################
                ]
                self.cursor.executemany('''
                    INSERT INTO projects (name, description, path, file, status, language)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', default_projects)
                self.conn.commit()

            # Optional: Insert some default data only if the database is empty
            self.cursor.execute("SELECT COUNT(*) FROM todo")
            if self.cursor.fetchone()[0] == 0:
                default_todo = [
                    ("i have a thing to do", 0, False, 1),
                    ("here is another thing!", 0, False, 1),
                    ("another thing, i have to do", 0, False, 1),
                ]
                self.cursor.executemany('''
                    INSERT INTO todo (description, priority, deleted, project_id)
                    VALUES (?, ?, ?, ?)
                ''', default_todo)
                self.conn.commit()


    def pull_card_data(self, title):
        # get cards, then append to the end of the query result the number of tasks the card has
        return [tuple(list(row) + [self.cursor.execute("SELECT COUNT(*) FROM todo WHERE project_id = ?;", (row[0],)).fetchone()[0]])
            for row in self.cursor.execute("SELECT * FROM projects WHERE status = ? ORDER BY LOWER(name);", (title,)).fetchall()]



# in_todo = False


class CommandWindow:
    def __init__(self,):
        self.h = HELP_HEIGHT
        self.w = SCREEN_WIDTH
        self.y = SCREEN_HEIGHT - HELP_HEIGHT
        self.x = 0
        self.win = curses.newwin(self.h, self.w, self.y, self.x)
        self.win.box()


class Window:
    def __init__(self, id, height, width, y, x, title, title_pos=2, color=c.WHITE, style=c.NORMAL):
        self.id = id
        self.h = height
        self.w = width
        self.y = y
        self.x = x
        self.win = curses.newwin(self.h, self.w, self.y, self.x)
        self.title = title
        self.color = color
        self.style = style
        self.title_pos = title_pos
        self.cards = []
        self.card_offset = 0
        # self.last_active = active_card

    def pull(self, dm):
        self.cards = [Card(id=card[0], # id
            height=INACTIVE_CARD_HEIGHT , width=self.w - (2 * X_PAD),y=self.y + Y_PAD, x=self.x + X_PAD,            # UI elements
            name=card[1], path=card[3], description=card[2], file=card[4], language=card[6], todo_count=card[7])    # Card data
                for card in dm.pull_card_data(self.title)]


    def has_cards(self):
        return len(self.cards) > 0

    def update(self, dm, active_window_id, active_card_index):

        self.card_offset = 0

        self.pull(dm)

        # TODO: only draw window once
        # draw this Window
        self.draw()

        # TODO: only activate necessary cards (below active one)
        # draw all Cards
        for i, card in enumerate(self.cards):
            if self.id == active_window_id and i == active_card_index:
                card.activate()

            card.draw(self.card_offset)
            self.card_offset += 3 if not card.active else 6


    # def regress(self):
    #     global active_window
    #     if active_window <= 1:
    #         return
    #     # self.cursor.execute('''
    #     #     UPDATE projects SET status = ? WHERE name = ?
    #     # ''', (windows[active_window - 1].title, windows[active_window].cards[active_card].name))
    #     active_window -= 1
    #     progress_card_name = self.cards[active_card].name
    #     self.pull()
    #     windows[active_window].pull()
    #     # self.conn.commit()
    #     self.draw()
    #     self.refresh()
    #     windows[active_window].activate_one(progress_card_name)
    #     windows[active_window].draw()
    #     windows[active_window].refresh()
    #     windows[HELP].draw_help()
    #     windows[HELP].refresh()
    #
    # def progress(self):
    #     global active_window
    #     if active_window >= 4:
    #         return
    #     # self.cursor.execute('''
    #     #     UPDATE projects SET status = ? WHERE name = ?
    #     # ''', (windows[active_window + 1].title, windows[active_window].cards[active_card].name))
    #     active_window += 1
    #     progress_card_name = self.cards[active_card].name
    #     self.pull()
    #     windows[active_window].pull()
    #     # self.conn.commit()
    #     self.draw()
    #     self.refresh()
    #     windows[active_window].activate_one(progress_card_name)
    #     windows[active_window].draw()
    #     windows[active_window].refresh()
    #     windows[HELP].draw_help()
    #     windows[HELP].refresh()

    def activate_one(self, name):
        global active_card
        for i, card in enumerate(self.cards):
            card.deactivate()
            if card.name == name:
                active_card = i
                card.activate()
                self.draw()
                self.refresh()

    def add_project(self):
        answers = self.draw_help(getting_input=True)
        if answers is not None:
            # self.cursor.execute('''
            #     INSERT INTO projects (name, description, path, file, status, language)
            #     VALUES (?, ?, ?, ?, 'Backlog', ?)
            # ''', (answers[0], answers[1], answers[2], answers[3], answers[4],))
            # self.conn.commit()
            windows[BACKLOG].pull()
            windows[BACKLOG].draw_cards()
            windows[BACKLOG].refresh()

    def delete_project(self):
        to_delete = windows[active_window].cards[active_card]
        # self.cursor.execute("DELETE FROM projects WHERE name = ?", (to_delete.name,))
        # self.conn.commit()
        windows[active_window].pull()
        windows[active_window].draw()
        windows[active_window].refresh()

    def edit_project(self):
        self.draw_help(getting_input=True, editting=True)
        windows[active_window].pull()
        windows[active_window].draw()
        windows[active_window].refresh()


# id, name, description, path, file, status, language

    # def draw_help(self, getting_input=False, editting=False):
    #     self.win.erase()
    #     self.win.attron(c.WHITE)
    #     self.win.box()
    #     self.win.attroff(c.WHITE)
    #     if in_todo:
    #         if getting_input:
    #             self.win.attron(c.BRIGHT_YELLOW | c.BOLD)
    #             if editting:
    #                 self.win.addstr(1, 3, "edit: ")
    #             else:
    #                 self.win.addstr(1, 4, "add: ")
    #             self.win.box()
    #             self.win.attroff(c.BRIGHT_YELLOW | c.BOLD)
    #             # self.win.addstr
    #             curses.echo()
    #             input = self.win.getstr(1, 9).decode("utf-8")
    #             curses.noecho()
    #             self.draw_help(False)
    #             return [input]
    #         else:
    #             strings = ["add", "delete", "edit", "quit"]
    #     else:
    #         if getting_input:
    #             questions = ["name*", "description", "path*", "file", "language"]
    #             if editting:
    #
    #                 self.win.attron(c.BRIGHT_YELLOW | c.BOLD)
    #                 self.win.box()
    #                 x = 4
    #                 prompt = "Column to edit: "
    #                 self.win.addstr(1, x, prompt)
    #                 x += len(prompt)
    #                 self.win.attroff(c.BRIGHT_YELLOW | c.BOLD)
    #                 for i, question in enumerate(questions):
    #
    #                     self.win.attron(c.ORANGE | c.BOLD)
    #                     prompt = f"{i+1}. "
    #                     self.win.addstr(1, x, prompt)
    #                     x += len(prompt)
    #                     self.win.attroff(c.ORANGE | c.BOLD)
    #
    #                     self.win.attron(c.WHITE)
    #                     prompt = f"{question} "
    #                     self.win.addstr(1, x, prompt)
    #                     x += len(prompt)
    #                     self.win.attroff(c.WHITE)
    #
    #                 self.win.attron(c.WHITE)
    #                 prompt = f" :  "
    #                 self.win.addstr(1, x, prompt)
    #                 x += len(prompt)
    #                 self.win.attroff(c.WHITE)
    #
    #                 curses.echo()
    #
    #                 self.win.attron(c.WHITE)
    #                 input = chr(self.win.getch(1, x))
    #                 self.win.attroff(c.WHITE)
    #
    #                 selection = 0
    #                 if input in ('1', '2', '3', '4', '5'):
    #                     selection = int(input) - 1
    #
    #                 edit_card = windows[active_window].cards[active_card]
    #                 existing_answers = [edit_card.name, edit_card.description, edit_card.path, edit_card.file, edit_card.language]
    #                 self.win.erase()
    #
    #                 x = 4
    #                 self.win.attron(c.BRIGHT_YELLOW | c.BOLD)
    #                 self.win.box()
    #                 prompt = f"Current value: "
    #                 self.win.addstr(1, x, prompt)
    #                 x += len(prompt)
    #                 self.win.attroff(c.BRIGHT_YELLOW | c.BOLD)
    #
    #                 self.win.attron(c.WHITE)
    #                 prompt = f"{existing_answers[selection]}  "
    #                 self.win.addstr(1, x, prompt)
    #                 x += len(prompt)
    #                 self.win.attroff(c.WHITE)
    #
    #                 self.win.attron(c.BRIGHT_YELLOW | c.BOLD)
    #                 prompt = f"New value: "
    #                 self.win.addstr(1, x, prompt)
    #                 x += len(prompt)
    #                 self.win.attroff(c.BRIGHT_YELLOW | c.BOLD)
    #
    #                 self.win.attron(c.WHITE)
    #                 input = self.win.getstr(1, x).decode("utf-8")
    #                 self.win.attroff(c.WHITE)
    #
    #                 # self.cursor.execute(f"UPDATE projects SET {questions[selection].strip("*")} = ? WHERE name = ?", (input, edit_card.name,))
    #                 # self.conn.commit()
    #
    #                 curses.noecho()
    #                 self.draw_help()
    #                 self.refresh()
    #                 return
    #                 # return ret
    #             else:
    #                 ret = []
    #                 for question in questions:
    #                     self.win.attron(c.BRIGHT_YELLOW | c.BOLD)
    #                     self.win.addstr(1, 4, question + ": ")
    #                     self.win.box()
    #                     self.win.attroff(c.BRIGHT_YELLOW | c.BOLD)
    #                     curses.echo()
    #                     input = self.win.getstr(1, 4 + len(question) + 2).decode("utf-8")
    #                     curses.noecho()
    #                     ret.append(input)
    #                     self.win.erase()
    #                 self.draw_help()
    #                 self.refresh()
    #                 return ret
    #
    #         strings = ["add", "delete", "edit", "cd", "nvim", "todo", "progress", "regress", "mode", "quit"]
    #
    #     y = 1
    #     x = 4
    #     for string in strings:
    #         self.win.addstr(y, x, f"{string[0]}: ", c.CYAN)
    #         x += 3
    #         if not in_todo and \
    #             ((active_window == 1 and string == "regress") \
    #             or (active_window == HELP-1 and string == "progress") \
    #             or (windows[active_window].cards[active_card].file in (None, "") and string == "nvim") \
    #             or (windows[active_window].cards[active_card].path == "" and string == "cd") \
    #             or (windows[active_window].cards[active_card].description in(None, "") and string == "description")):
    #             color = c.DARK_GREY
    #         else:
    #             color = c.WHITE
    #         self.win.addstr(y, x, f"{string}", color)
    #         x += len(string) + 5


    def draw_cards(self):
        shove = False
        for card in self.cards:
            card.win.erase()
            if card.active:
                card.height = 6
                card.active = True
                card.color = c.WHITE
                card.unshove()
                shove = True # aka found active
            else:
                card.height = 3
                card.active = False
                card.color = c.WHITE
                if shove:
                    card.shove()
                    card.is_shoved = True
            card.win.resize(card.height, card.width - 4)

            current_mode = "normal"
            if current_mode == "normal":
                card.win.attron(c.DIM_WHITE | c.BOLD) if card.active else card.win.attron(c.DARK_GREY | c.BOLD)
                card.win.box()
                card.draw_name_border()
                card.win.attroff(c.DIM_WHITE | c.BOLD)
            elif current_mode == "colored":
                if card.todo_count == 0:
                    card.win.attron(c.GUTTER)
                elif card.todo_count <= 2:
                    card.win.attron(c.LIGHT_GREEN)
                elif card.todo_count <= 5:
                    card.win.attron(c.YELLOW)
                else:
                    card.win.attron(c.LIGHT_RED)
                card.win.box()
                card.draw_name_border()
                card.win.attroff(c.GUTTER | c.GREEN | c.BRIGHT_YELLOW | c.RED)

            card.win.attron(card.color | c.BOLD)
            card.win.addstr(1, 2, card.name)
            card.win.addstr(1, card.width - 4 - len(card.language) - 2, f"{card.language}") if card.language not in (None, "") else ""

            card.win.attroff(card.color | c.BOLD)
            if card.active:
                card.win.attron(c.WHITE)
                start_desc = (card.width // 2) - (len(card.description) // 2) - 2 
                card.win.addstr(3, start_desc, f"{card.description}")
                card.win.attron(c.DARK_GREY)
                card.win.addstr(4, card.width - 4 - len("items: ") - 2 - len(str(card.todo_count)), "items: ")
                card.win.attroff(c.DARK_GREY)
                if card.todo_count <= 2:
                    card.win.attron(c.GREEN)
                elif card.todo_count <= 5:
                    card.win.attron(c.BRIGHT_YELLOW)
                else:
                    card.win.attron(c.RED)
                card.win.attron(c.BOLD)
                card.win.addstr(4, card.width - 4 - len(str(card.todo_count)) - 2, f"{card.todo_count}")
                card.win.attroff(c.GREEN | c.BRIGHT_YELLOW | c.RED | c.BOLD)

            card.refresh()

    def draw(self):
        self.win.attron(self.color | self.style)
        self.win.box()
        self.win.addstr(0, self.title_pos, f" {self.title}{" (" + str(len(self.cards)) + ") " if self.id not in (FRAME, HELP) else " "}" if self.title != "" else "")
        self.win.attroff(self.color | self.style)
        if self.id == HELP:
            self.draw_help()
        self.win.refresh()

        # self.draw_cards()

    def refresh(self):
        self.win.refresh()


class Card():
    def __init__(self, id, height, width, y, x, name, path, description="", file="", language="", todo_count=0):
        self.id = id
        self.h = height
        self.w = width
        self.y = y
        self.x = x
        self.win = curses.newwin(self.h, self.w, self.y, self.x)
        self.name = name
        self.path = path
        self.file = file
        self.description = description
        self.language = language
        self.todo_count = todo_count
        self.active = False
        self.text_color = c.WHITE
        self.is_shoved = False
        self.is_scrunched = False
        self.todo_window = None
        self.items = []
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.selected_item = 0

    def clear(self):
        self.win.erase()

    def draw(self, y_offset):
        self.win.mvwin(self.y + y_offset, self.x)
        self.win.box()

        self.win.addstr(Y_PAD, X_PAD, self.name, self.text_color | c.BOLD)
        self.win.addstr(Y_PAD, self.w - len(self.language) - X_PAD, self.language, self.text_color | c.BOLD)
        if self.active:
            self.draw_name_border()
        self.win.refresh()

    def activate(self):
        self.active = True
        self.win.resize(ACTIVE_CARD_HEIGHT, self.w)

    def deactivate(self):
        self.active = False
        self.win.resize(INACTIVE_CARD_HEIGHT, self.w)

    def shove(self, force=False):
        if not self.is_shoved or force:
            self.win.mvwin(self.y + 4, self.x)

    def draw_name_border(self):
        if self.active:
            self.win.addch(2, 0, '├')
            self.win.addch(0, len(self.name) + 3, '┬')
            self.win.addch(2, len(self.name) + 3, '┘')
            self.win.addch(1, len(self.name) + 3, '│')
            self.win.addstr(2, 1, '─' * (len(self.name) + 2))


    def unshove(self):
        if self.is_shoved:
            self.win.mvwin(self.y + 1, self.x)

    def open_todo(self):
        # global in_todo
        in_todo = True
        
        self.win.attron(c.PURPLE)
        self.win.box()
        self.draw_name_border()
        self.win.attroff(c.PURPLE)
        self.win.refresh()

        windows[HELP].draw_help()
        windows[HELP].refresh()
        
        self.items = []
        longest_item = 37
        self.cursor.execute("SELECT * FROM todo WHERE project_id = ?", (self.id,))
        # id, description, priority, deleted, project_id
        rows = self.cursor.fetchall()
        for row in rows:
            if row[3] != True: # deleted
                self.items.append((row[0], row[1]))
                longest_item = max(len(row[1]) + 4 + 2 + 5, longest_item)

        h, w = min(len(rows) + 3 + 2, windows[active_window].h), longest_item
        # y, x = 2, stdscr.getmaxyx()[1] // 2 - (w // 2)
        y, x = windows[active_window].cards[active_card].y + 1 , self.x + 35 if active_window < ACTIVE else self.x - 39
        self.todo_window = curses.newwin(h, w, y, x)
        self.todo_window.attron(c.PURPLE | c.BOLD)
        self.todo_window.box()
        self.todo_window.attroff(c.PURPLE)
        self.todo_window.attron(c.WHITE)
        self.todo_window.addstr(1, 2, "TODO:")
        self.todo_window.attroff(c.WHITE | c.BOLD)

        item_y = 3
        for i, item in enumerate(self.items):
            if i == self.selected_item:
                self.todo_window.attron(c.INVERT)
            else:
                self.todo_window.attron(c.WHITE)

            self.todo_window.addstr(item_y, 4, "• " + item[1])
            item_y += 1
            if i == self.selected_item:
                self.todo_window.attroff(c.INVERT)
            else:
                self.todo_window.attroff(c.WHITE)
        self.todo_window.attroff(c.WHITE | c.BOLD)
        # self.todo_count = len(rows)
        # self.todo_window.addstr(0, self.title_pos, f" {self.title}{" (" + str(len(self.cards)) + ") " if self.id not in (FRAME, HELP) else " "}" if self.title != "" else "")
        self.todo_window.refresh()
        # cursor.execute('''
        # ''')

    def close_todo(self):
        global in_todo
        in_todo = False
        if self.todo_window:
            self.todo_window.clear()
            self.todo_window = None
            self.items = []
        draw_windows()

    def add_item(self):
        new_item = windows[HELP].draw_help(getting_input=True)[0]
        if self.todo_window:
            self.cursor.execute("INSERT INTO todo (description, priority, deleted, project_id) VALUES (?, ?, ?, ?)", (new_item, 0, False, self.id))
            self.conn.commit()
            self.todo_count += 1
            draw_windows() # TODO: basically eliminate this
            self.refresh()
            self.close_todo()
            self.open_todo()

    def down(self):
        if self.todo_window and self.selected_item < self.todo_count - 1:
            self.selected_item += 1
            self.refresh()
            self.close_todo()
            self.open_todo()
            

    def up(self):
        if self.todo_window and self.selected_item > 0:
            self.selected_item -= 1
            self.refresh()
            self.close_todo()
            self.open_todo()

    def delete_item(self):
        if self.todo_count <= 0:
            return
        self.cursor.execute("DELETE FROM todo WHERE description = ?", (self.items[self.selected_item][1],))
        self.conn.commit()
        self.todo_count -= 1
        if self.selected_item > 0:
            self.selected_item -= 1
        self.close_todo()
        self.open_todo()
        pass

    def edit_item(self, ):
        if self.todo_count <= 0:
            return
        item_text = windows[HELP].draw_help(getting_input=True, editting=True)[0]
        self.cursor.execute("UPDATE todo SET description = ? WHERE description = ?", (item_text, self.items[self.selected_item][1],))
        self.conn.commit()
        self.refresh()
        self.close_todo()
        self.open_todo()



def init():
    stdscr.clear()

    curses.curs_set(0)
    curses.noecho()
    curses.set_escdelay(1)
    stdscr.keypad(True)

    stdscr.refresh()

    FRAME_WINDOW = Window(FRAME, SCREEN_HEIGHT - HELP_HEIGHT, SCREEN_WIDTH,  0, 0, HEADER, title_pos=(SCREEN_WIDTH // 2) - (len(HEADER) // 2 - 1)),

    WINDOWS.extend([
        Window(ABANDONED,  SECTION_HEIGHT, SECTION_WIDTH, Y_PAD, ((ABANDONED) * SECTION_WIDTH) + (ABANDONED * X_PAD),   STATUSES[ABANDONED][0], color=STATUSES[ABANDONED][1]),
        Window(BACKLOG,    SECTION_HEIGHT, SECTION_WIDTH, Y_PAD, ((BACKLOG)   * SECTION_WIDTH) + (BACKLOG   * X_PAD),   STATUSES[BACKLOG][0],   color=STATUSES[BACKLOG][1]),
        Window(ACTIVE,     SECTION_HEIGHT, SECTION_WIDTH, Y_PAD, ((ACTIVE)    * SECTION_WIDTH) + (ACTIVE    * X_PAD),   STATUSES[ACTIVE][0],    color=STATUSES[ACTIVE][1]),
        Window(DONE,       SECTION_HEIGHT, SECTION_WIDTH, Y_PAD, ((DONE)      * SECTION_WIDTH) + (DONE      * X_PAD),   STATUSES[DONE][0],      color=STATUSES[DONE][1])
                    ])

    HELP_WINDOW = CommandWindow()

    # Connect to database (or create it if it doesn't exist)
    if sys.argv[0][-3:] == ".py":
        conn = sqlite3.connect(DB_PATH)
    else:
        # conn = sqlite3.connect(PROD_DB_PATH)
        conn = sqlite3.connect(DB_PATH)
        
    dm = DatabaseManager(conn)
    dm.init()

    sm = StateManager(dm)
    sm.init()

    return sm, dm


def main(stdscr):
    sm, dm = init()

    todo_keymap = {
        "q": lambda: windows[active_window].cards[active_card].close_todo(),

        "a": lambda: windows[active_window].cards[active_card].add_item(),

        "KEY_UP": lambda: windows[active_window].cards[active_card].up(),
        "KEY_DOWN": lambda: windows[active_window].cards[active_card].down(),
        "d": lambda: windows[active_window].cards[active_card].delete_item(),
        "e": lambda: windows[active_window].cards[active_card].edit_item(),
    }

    keymap = {
        "q": lambda: exit(0),
        "\x1b": lambda: exit(0),

        "a": lambda:  windows[HELP].add_project(),
        "d": lambda:  windows[HELP].delete_project(),
        "e": lambda:  windows[HELP].edit_project(),

        "c": lambda: os.system(TERMINAL_PREFIX + windows[active_window].cards[active_card].path),
        "n": lambda: os.system(TERMINAL_PREFIX + windows[active_window].cards[active_card].path + " -- bash -c \'" +  NEOVIM_PREFIX + windows[active_window].cards[active_card].file + "\'") if windows[active_window].cards[active_card].file != "" else "",
        "t": lambda: windows[active_window].cards[active_card].open_todo(),
        "p": lambda: windows[active_window].progress(),
        "r": lambda: windows[active_window].regress(),

        "KEY_LEFT": lambda: sm.left(),
        "KEY_RIGHT": lambda: sm.right(),
        "KEY_UP": lambda: sm.up(),
        "KEY_DOWN": lambda: sm.down(),

        "m": lambda: sm.next_mode(),

        # "": lambda: ,
    }

    # Main loop
    while True:
        # get and handle input
        key = stdscr.getkey()
        # if in_todo:
        #     if key not in todo_keymap: continue
        #     todo_keymap[key]()
        # else: 
        if key not in keymap: continue
        keymap[key]()


if __name__ == "__main__":
    curses.wrapper(main)

