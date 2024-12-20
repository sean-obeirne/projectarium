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
bright_yellow = hex_to_rgb("ffd75e")
bright_blue = hex_to_rgb("3169f1")


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
COLOR_GUTTER = 5
COLOR_CYAN = 6
COLOR_WHITE = 7
COLOR_DARK_GREY = 8
COLOR_LIGHT_RED = 9
COLOR_LIGHT_GREEN = 10
COLOR_YELLOW = 11
COLOR_LIGHT_BLUE = 12
COLOR_PURPLE = 13
COLOR_BRIGHT_YELLOW = 14
COLOR_DIM_WHITE = 15

# RGB values (0-1000 scale)
color_definitions = {
    COLOR_BLACK: tn_terminal_black,
    COLOR_RED: tn_red1,
    COLOR_GREEN: green,
    COLOR_ORANGE: tn_orange,
    COLOR_BLUE: bright_blue,
    COLOR_GUTTER: tn_fg_gutter,
    COLOR_CYAN: tn_cyan,
    COLOR_WHITE: white,
    COLOR_DARK_GREY: tn_dark5,
    COLOR_LIGHT_RED: tn_red,
    COLOR_LIGHT_GREEN: tn_green,
    COLOR_YELLOW: tn_yellow,
    COLOR_LIGHT_BLUE: tn_blue,
    COLOR_PURPLE: tn_purple,
    COLOR_BRIGHT_YELLOW: bright_yellow,
    COLOR_DIM_WHITE: tn_fg,
}



# Initialize 16 colors
def init_16_colors():
    curses.start_color()
    
    if curses.can_change_color():
        for color, rgb in color_definitions.items():
            curses.init_color(color, *rgb)
    
    # Define color pairs using custom color numbers
    curses.init_pair(1, COLOR_WHITE, COLOR_GUTTER)
    curses.init_pair(2, COLOR_RED, -1)
    curses.init_pair(3, COLOR_GREEN, -1)
    curses.init_pair(4, COLOR_ORANGE, -1)
    curses.init_pair(5, COLOR_BLUE, -1)
    curses.init_pair(6, COLOR_GUTTER, -1)
    curses.init_pair(7, COLOR_CYAN, -1)
    curses.init_pair(8, COLOR_WHITE, -1)
    curses.init_pair(9, COLOR_DARK_GREY, -1)
    curses.init_pair(10, COLOR_LIGHT_RED, -1)
    curses.init_pair(11, COLOR_LIGHT_GREEN, -1)
    curses.init_pair(12, COLOR_YELLOW, -1)
    curses.init_pair(13, COLOR_LIGHT_BLUE, -1)
    curses.init_pair(14, COLOR_PURPLE, -1)
    curses.init_pair(15, COLOR_BRIGHT_YELLOW, -1)
    curses.init_pair(16, COLOR_DIM_WHITE, -1)

init_16_colors()

INVERT = curses.color_pair(1)
RED = curses.color_pair(2)
GREEN = curses.color_pair(3)
ORANGE = curses.color_pair(4)
BLUE = curses.color_pair(5)
GUTTER = curses.color_pair(6)
CYAN = curses.color_pair(7)
WHITE = curses.color_pair(8)
DARK_GREY = curses.color_pair(9)
LIGHT_RED = curses.color_pair(10)
LIGHT_GREEN = curses.color_pair(11)
YELLOW = curses.color_pair(12)
LIGHT_BLUE = curses.color_pair(13)
PURPLE = curses.color_pair(14)
BRIGHT_YELLOW = curses.color_pair(15)
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

DB_PATH = "/home/sean/bin/.projectarium.db"
# DB_PATH = ".projectarium.db"

FRAME = 0
ABANDONED = 1
BACKLOG = 2
ACTIVE = 3
DONE = 4
HELP = 5

statuses = {
    ABANDONED: (RED, "Abandoned"),
    BACKLOG: (BLUE, "Backlog"),
    ACTIVE: (BRIGHT_YELLOW, "Active"),
    DONE: (GREEN, "Done"),
}
modes = ["normal", "colored"]
current_mode = modes[0]
def shift_mode():
    global current_mode
    if current_mode == "normal":
        current_mode = "colored"
        draw_windows()
    else:
        current_mode = "normal"
        draw_windows()

windows = []
def draw_windows():
    for window in windows:
        window.draw()

in_todo = False

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
            self.cursor.execute("SELECT COUNT(*) FROM todo WHERE project_id = ?;", (row[0],))
            todo_count = self.cursor.fetchone()[0]
            self.cards.append(Card(row[0], 3, self.w, self.y + self.card_offset, self.x + 2, row[1], row[3], row[4], row[2], row[6], todo_count=todo_count))
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

    def add_project(self):
        answers = self.draw_help(getting_input=True)
        if answers is not None:
            self.cursor.execute('''
                INSERT INTO projects (name, description, path, file, status, language)
                VALUES (?, ?, ?, ?, 'Backlog', ?)
            ''', (answers[0], answers[1], answers[2], answers[3], answers[4],))
            self.conn.commit()
            windows[BACKLOG].pull()
            windows[BACKLOG].draw_cards()
            windows[BACKLOG].refresh()

    def delete_project(self):
        to_delete = windows[active_window].cards[active_card]
        self.cursor.execute("DELETE FROM projects WHERE name = ?", (to_delete.name,))
        self.conn.commit()
        windows[active_window].pull()
        windows[active_window].draw()
        windows[active_window].refresh()

    def edit_project(self):
        to_edit = windows[active_window].cards[active_card]
        answers = self.draw_help(getting_input=True, editting=True)
        if answers is not None:
            windows[BACKLOG].pull()
            windows[BACKLOG].draw_cards()
            windows[BACKLOG].refresh()


# id, name, description, path, file, status, language

    def draw_help(self, getting_input=False, editting=False):
        self.win.erase()
        self.win.attron(WHITE)
        self.win.box()
        self.win.attroff(WHITE)
        if in_todo:
            if getting_input:
                self.win.attron(BRIGHT_YELLOW | BOLD)
                if editting:
                    self.win.addstr(1, 3, "edit: ")
                else:
                    self.win.addstr(1, 4, "add: ")
                self.win.box()
                self.win.attroff(BRIGHT_YELLOW | BOLD)
                # self.win.addstr
                curses.echo()
                input = self.win.getstr(1, 9).decode("utf-8")
                curses.noecho()
                self.draw_help(False)
                return [input]
            else:
                strings = ["add", "delete", "edit", "quit"]
        else:
            if getting_input:
                questions = ["name*", "description", "path*", "file", "language"]
                if editting:
                    pass
                #     edit_card = windows[active_window].cards[active_card]
                #     existing_answers = [edit_card.name, edit_card.description, edit_card.path, edit_card.file, edit_card.language]
                #     self.cursor.execute("SELECT * FROM projects WHERE name = ?", (edit_card.name,))
                #     fetched = self.cursor.fetchone()[1:]
                #     ret = []
                #     curses.echo()
                #
                #
                #     for i in range(len(questions)):
                #         self.win.erase()
                #
                #         self.win.attron(BRIGHT_YELLOW | BOLD)
                #         self.win.box()
                #         x = 4
                #         prompt = f"current {questions[i]}: "
                #         self.win.addstr(1, x, prompt)
                #         x += len(prompt)
                #         self.win.attroff(BRIGHT_YELLOW | BOLD)
                #
                #         self.win.attron(WHITE)
                #         prompt = f"{existing_answers[i]}"
                #         self.win.addstr(1, x, prompt)
                #         x += len(prompt)
                #         self.win.attroff(WHITE)
                #
                #         self.win.attron(BRIGHT_YELLOW | BOLD)
                #         prompt = f", new {questions[i]} (_ for no change): "
                #         self.win.addstr(1, x, prompt)
                #         x += len(prompt)
                #         self.win.attroff(BRIGHT_YELLOW | BOLD)
                #
                #         self.win.attron(WHITE)
                #         input = self.win.getstr(1, x).decode("utf-8")
                #         self.win.attroff(WHITE)
                #         if input != "_" and input != existing_answers[i]:
                #             self.cursor.execute(f"UPDATE projects SET {questions[i].strip('*')} = ? WHERE name = ?", (input, existing_answers[0],))
                #             self.conn.commit()
                #             
                #
                #     curses.noecho()
                #     self.draw_help()
                #     self.refresh()
                #     return ret
                else:
                    ret = []
                    for question in questions:
                        self.win.attron(BRIGHT_YELLOW | BOLD)
                        self.win.addstr(1, 4, question + ": ")
                        self.win.box()
                        self.win.attroff(BRIGHT_YELLOW | BOLD)
                        curses.echo()
                        input = self.win.getstr(1, 4 + len(question) + 2).decode("utf-8")
                        curses.noecho()
                        ret.append(input)
                        self.win.erase()
                    self.draw_help()
                    self.refresh()
                    return ret

            strings = ["cd", "nvim", "todo", "progress", "regress", "mode", "quit"]

        y = 1
        x = 4
        for string in strings:
            self.win.addstr(y, x, f"{string[0]}: ", CYAN)
            x += 3
            if not in_todo and \
                ((active_window == 1 and string == "regress") \
                or (active_window == HELP-1 and string == "progress") \
                or (windows[active_window].cards[active_card].file in (None, "") and string == "nvim") \
                or (windows[active_window].cards[active_card].path == "" and string == "cd") \
                or (windows[active_window].cards[active_card].description in(None, "") and string == "description")):
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
                card.color = WHITE
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

            if current_mode == "normal":
                card.win.attron(DIM_WHITE | BOLD) if card.active else card.win.attron(DARK_GREY | BOLD)
                card.win.box()
                card.draw_name_border()
                card.win.attroff(DIM_WHITE | BOLD)
            elif current_mode == "colored":
                if card.todo_count == 0:
                    card.win.attron(GUTTER)
                elif card.todo_count <= 2:
                    card.win.attron(LIGHT_GREEN)
                elif card.todo_count <= 5:
                    card.win.attron(YELLOW)
                else:
                    card.win.attron(LIGHT_RED)
                card.win.box()
                card.draw_name_border()
                card.win.attroff(GUTTER | GREEN | BRIGHT_YELLOW | RED)

            card.win.attron(card.color | BOLD)
            card.win.addstr(1, 2, card.name)
            card.win.addstr(1, card.width - 4 - len(card.language) - 2, f"{card.language}") if card.language not in (None, "") else ""

            card.win.attroff(card.color | BOLD)
            if card.active:
                card.win.attron(WHITE)
                start_desc = (card.width // 2) - (len(card.description) // 2) - 2 
                card.win.addstr(3, start_desc, f"{card.description}")
                card.win.attron(DARK_GREY)
                card.win.addstr(4, card.width - 4 - len("items: ") - 2 - len(str(card.todo_count)), "items: ")
                card.win.attroff(DARK_GREY)
                if card.todo_count <= 2:
                    card.win.attron(GREEN)
                elif card.todo_count <= 5:
                    card.win.attron(BRIGHT_YELLOW)
                else:
                    card.win.attron(RED)
                card.win.attron(BOLD)
                card.win.addstr(4, card.width - 4 - len(str(card.todo_count)) - 2, f"{card.todo_count}")
                card.win.attroff(GREEN | BRIGHT_YELLOW | RED | BOLD)

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
    def __init__(self, id, height, width, y, x, name, path, file="", description="", language="", todo_count=0):
        self.id = id
        self.height = height
        self.width = width
        self.y = y
        self.x = x
        self.win = curses.newwin(self.height, self.width - 4, self.y + 1, self.x)
        self.name = name
        self.path = path
        self.file = file
        self.description = description
        self.language = language
        self.todo_count = todo_count
        self.active = False
        self.color = WHITE
        self.is_shoved = False
        self.is_scrunched = False
        self.todo_window = None
        self.items = []
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.selected_item = 0

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
        global in_todo
        in_todo = True
        
        self.win.attron(PURPLE)
        self.win.box()
        self.draw_name_border()
        self.win.attroff(PURPLE)
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
        self.todo_window.attron(PURPLE | BOLD)
        self.todo_window.box()
        self.todo_window.attroff(PURPLE)
        self.todo_window.attron(WHITE)
        self.todo_window.addstr(1, 2, "TODO:")
        self.todo_window.attroff(WHITE | BOLD)

        item_y = 3
        for i, item in enumerate(self.items):
            if i == self.selected_item:
                self.todo_window.attron(INVERT)
            else:
                self.todo_window.attron(WHITE)

            self.todo_window.addstr(item_y, 4, "• " + item[1])
            item_y += 1
            if i == self.selected_item:
                self.todo_window.attroff(INVERT)
            else:
                self.todo_window.attroff(WHITE)
        self.todo_window.attroff(WHITE | BOLD)
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
            description TEXT CHECK(LENGTH(description) <= 29),
            path TEXT NOT NULL,
            file TEXT,
            status TEXT NOT NULL,
            language TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS todo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL UNIQUE,
            priority TEXT,
            deleted BOOLEAN NOT NULL DEFAULT 0,
            project_id,
            FOREIGN KEY (project_id) REFERENCES projects (id)
        )
    ''')

    # Optional: Insert some default data only if the database is empty
    cursor.execute("SELECT COUNT(*) FROM projects")
    if cursor.fetchone()[0] == 0:
        default_projects = [
            ("WotR",            "Wizards of the Rift",          "/home/sean/code/paused/godot/Wizards-of-the-Rift/","",                 "Abandoned",  "Godot"),
            ("LearnScape",      "General learning visualizer",  "/home/sean/code/paused/LearnScape/",               "learnscape.py",    "Abandoned",  "Python"),
            ("ROMs",            "ROM emulation optimization",   "/home/sean/code/future/ROMs/",                     "",                 "Backlog",      "C"),
            ("goverse",         "Go VCS application",           "/home/sean/code/active/go/goverse/",               "cli/main.go",      "Active",       "Go"),
            ("projectarium",    "Project progress tracker",     "/home/sean/code/active/python/projectarium/",      "projectarium.py",  "Active",       "Python"),
            ("snr",             "Search and replace plugin",    "/home/sean/.config/nvim/lua/snr/",                 "init.lua",         "Active",       "Lua"),
            ("todua",           "Todo list for Neovim",         "/home/sean/.config/nvim/lua/todua/",               "init.lua",         "Active",       "Lua"),
            ("macro-blues",     "Custom macropad firmware",     "/home/sean/code/active/c/macro-blues/",            "macro-blues",      "Active",       "C"),
            ("leetcode",        "Coding interview practice",    "/home/sean/code/paused/leetcode/",                 "",                 "Active",       "Python"),
            ("TestTaker",       "ChatGPT->Python test maker",   "/home/sean/code/paused/TestTaker/",                "testtaker.py",     "Active",       "Python"),
            ("Mission-Uplink",  "TFG Mission Uplink",           "/home/sean/code/tfg/Mission-Uplink/",              "README.md",        "Active",       "Go,C"),
            ("Sorter",          "Sorting algoithm visualizer",  "/home/sean/code/done/Sorter/",                     "sorter.py",        "Done",         "Python"),
            ("landing-page",    "Cute application launcher",    "/home/sean/code/done/landing-page/",               "landing-page.py",  "Done",         "Python"),
            ################"   valid description length  "################################################################################################
        ]
        cursor.executemany('''
            INSERT INTO projects (name, description, path, file, status, language)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', default_projects)
    # Optional: Insert some default data only if the database is empty
    cursor.execute("SELECT COUNT(*) FROM todo")
    if cursor.fetchone()[0] == 0:
        default_todo = [
            ("i have a thing to do", 0, False, 1),
            ("here is another thing!", 0, False, 1),
            ("another thing, i have to do", 0, False, 1),
        ]
        cursor.executemany('''
            INSERT INTO todo (description, priority, deleted, project_id)
            VALUES (?, ?, ?, ?)
        ''', default_todo)

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

    " ": lambda: draw(),

    "a": lambda:  windows[HELP].add_project(),
    "d": lambda:  windows[HELP].delete_project(),
    # "e": lambda:  windows[HELP].edit_project(),

    "c": lambda: os.system(TERMINAL_PREFIX + windows[active_window].cards[active_card].path),
    "n": lambda: os.system(TERMINAL_PREFIX + windows[active_window].cards[active_card].path + " -- bash -c \'" +  NEOVIM_PREFIX + windows[active_window].cards[active_card].file + "\'") if windows[active_window].cards[active_card].file != "" else "",
    "t": lambda: windows[active_window].cards[active_card].open_todo(),
    "p": lambda: windows[active_window].progress(),
    "r": lambda: windows[active_window].regress(),

    "KEY_LEFT": lambda: decrement_active_window(),
    "KEY_RIGHT": lambda: increment_active_window(),
    "KEY_UP": lambda: decrement_active_card(),
    "KEY_DOWN": lambda: increment_active_card(),

    "m": lambda: shift_mode(),

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
        if in_todo:
            if key not in todo_keymap: continue
            todo_keymap[key]()
        else: 
            if key not in keymap: continue
            keymap[key]()

        # if key == 'a':
        #     add_card("another", "/some/path")
        #     continue

if __name__ == "__main__":
    curses.wrapper(main)

