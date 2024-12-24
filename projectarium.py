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
ABANDONED = 0
BACKLOG = 1
ACTIVE = 2
DONE = 3
HELP = 4
STATUSES = {
    "Abandoned":    c.RED,
    "Backlog":      c.BLUE,
    "Active":       c.BRIGHT_YELLOW,
    "Done":         c.GREEN,
}


# Assign other variables
PROD_DB_PATH = "/home/sean/bin/.projectarium.db"
DB_PATH = ".projectarium.db"
TERMINAL_PREFIX = "gnome-terminal --maximize --working-directory="
NEOVIM_PREFIX = "nvim "


# UI dimensions
SCREEN_HEIGHT, SCREEN_WIDTH = stdscr.getmaxyx()
Y_PAD                   = 1
X_PAD                   = 2
COMMAND_WINDOW_HEIGHT   = 3
SECTION_HEIGHT          = (SCREEN_HEIGHT - COMMAND_WINDOW_HEIGHT)
SECTION_WIDTH           = (SCREEN_WIDTH - (3 * X_PAD)) // 4 # right-hand padding
WINDOWS                 = []
COMMAND_WINDOW          = None
INACTIVE_CARD_HEIGHT    = 3
ACTIVE_CARD_HEIGHT      = 6

NO_TODO_ITEMS       = 0
LOW_TODO_ITEMS      = 3
MEDIUM_TODO_ITEMS   = 6
MAX_TODO_ITEMS      = 99
REGULAR             = 0
DARK                = 1
TODO_COLORS = [(NO_TODO_ITEMS, REGULAR, c.DIM_WHITE), (LOW_TODO_ITEMS, REGULAR, c.GREEN), (MEDIUM_TODO_ITEMS, REGULAR, c.BRIGHT_YELLOW), (MAX_TODO_ITEMS, REGULAR, c.RED),
               (NO_TODO_ITEMS, DARK, c.GUTTER), (LOW_TODO_ITEMS, DARK, c.LIGHT_GREEN), (MEDIUM_TODO_ITEMS, DARK, c.YELLOW), (MAX_TODO_ITEMS, DARK, c.LIGHT_RED)
               ]
color_code = lambda tc, s: [color for limit, shade, color in TODO_COLORS if tc <= limit and s == shade][0]


MODES               =  [BLAND := 0, COLORED := 1, DIM := 2]

COMMAND_STATES      =  [ADD := 0,   DELETE := 1,  EDIT := 2, SELECT := 3]
EDIT_PROJECT_CHOICES   =  ["name", "description", "path", "file", "language"]

# Global helper function
def draw_box(window, attributes):
    window.attron(attributes)
    window.box()
    window.attroff(attributes)

           
class StateManager:
    def __init__(self, dm, cw):
        self.dm = dm
        self.cw = cw
        self.tm = None
        self.active_window = 0
        self.active_card = -1
        self.mode = COLORED
        self.in_todo = False

    def init(self):
        for window in WINDOWS:
            window.pull(self.dm)
            if self.active_card == -1 and len(window.cards) > 0:
                self.active_window = window.id
                self.active_card = 0
                self.get_active_card().activate()
                break
        self.update_windows()

    def update_windows(self): # TODO: only update active window and new active window
        for window in WINDOWS:
            window.update(self.dm, self.active_window, self.active_card, self.mode)
        self.cw.help(self.active_window, self.get_active_card(), self.in_todo)

    def update_window(self, window_id=None):
        window_id = self.active_window if window_id is None else window_id
        WINDOWS[window_id].update(self.dm, window_id, self.active_card)

    def get_cards(self):
        return WINDOWS[self.active_window].cards

    def get_active_card(self):
        if len(self.get_cards()) > 0:
            return WINDOWS[self.active_window].cards[self.active_card]
        else:
            return Card(-1, 0, 0, 0, 0, "", "", "", "", "") # dummy card to fool linter

    def open_dir(self):
        os.system(TERMINAL_PREFIX + self.get_active_card().path)

    def open_nvim(self):
          os.system(TERMINAL_PREFIX + self.get_active_card().path + " -- bash -c \'" +  NEOVIM_PREFIX + self.get_active_card().file + "\'") if self.get_active_card().file != "" else "",

    def open_both(self):
        self.open_dir()
        self.open_nvim()

    def set_mode(self, new_mode):
        self.mode = new_mode
        self.update_windows()

    def next_mode(self):
        self.mode = (self.mode + (2 if self.mode == 1 else 1)) % len(MODES)
        self.update_windows()

    def open_todo(self):
        self.tm = TodoManager(self.active_window, self.get_active_card(), self.dm.pull_todo_data(self.get_active_card().id))
        self.in_todo = True
        self.cw.help(self.active_window, self.get_active_card(), self.in_todo)
        self.set_mode(DIM)
        self.update_windows()
        self.tm.draw()

    def quit_todo(self):
        if self.tm: self.tm.close()
        self.update_windows()
        self.in_todo = False
        self.set_mode(COLORED)
        self.cw.help(self.active_window, self.get_active_card(), self.in_todo)

    def hide_todo(self):
        if self.tm: self.tm.close()

    def navigate(self, move, get_new_active_card=None):
        if self.in_todo: self.hide_todo()
        move()
        if get_new_active_card is not None: 
            self.active_card = get_new_active_card()
        self.update_windows()
        if self.in_todo: self.open_todo()

    def up(self):
        if self.active_card > 0:
            self.navigate(lambda: setattr(self, "active_card", self.active_card - 1))

    def down(self):
        if self.active_card < len(self.get_cards()) - 1:
            self.navigate(lambda: setattr(self, "active_card", self.active_card + 1))

    def right(self):
        if self.active_window < 3:
            self.navigate(lambda: setattr(self, "active_window", self.active_window + 1),
                          lambda: min(self.active_card, max(len(self.get_cards()) - 1, 0)))

    def left(self):
        if self.active_window > 0:
            self.navigate(lambda: setattr(self, "active_window", self.active_window - 1), 
                          lambda: min(self.active_card, max(len(self.get_cards()) - 1, 0)))


    def progress(self):
        card = WINDOWS[self.active_window].cards[self.active_card]
        if self.active_window >= 3: return
        self.dm.progress(card.name, self.active_window)
        self.update_windows()
        self.up()
        if len(self.get_cards()) == 0:
            self.right()
        
    def regress(self):
        card = WINDOWS[self.active_window].cards[self.active_card]
        if self.active_window <= 0: return
        self.dm.regress(card.name, self.active_window)
        self.update_windows()
        self.up()
        if len(self.get_cards()) == 0:
            self.left()
        
    def add_item(self):
        if self.tm:
            self.tm.update_tm(self.dm.add_item(self.cw.get_input("New todo item", ADD, ""), self.get_active_card().id))
            self.update_windows()
            self.tm.draw()

    def edit_item(self):
        if self.tm and self.get_active_card().todo_count > 0:
            new_description = self.cw.get_input("Description", EDIT, self.tm.todo_list[self.tm.selected_item][1])
            todo_id = self.tm.todo_list[self.tm.selected_item][0]
            self.tm.update_tm(self.dm.edit_item(todo_id, new_description, self.get_active_card().id))
            self.update_windows()
            self.tm.draw()

    def delete_item(self):
        if self.tm and self.get_active_card().todo_count > 0:
            self.tm.update_tm(self.dm.delete_item(self.tm.todo_list[self.tm.selected_item][0], self.get_active_card().id))
            self.update_windows()
            self.tm.draw()

    def add_project(self):
        name = self.cw.get_input("Name", ADD, "")
        description = self.cw.get_input("Description", ADD, "")
        path = self.cw.get_input("Path", ADD, "")
        file = self.cw.get_input("File", ADD, "")
        language = self.cw.get_input("Language", ADD, "")
        self.dm.add_project(name, description, path, file, "Backlog", language)
        self.update_windows()

    def edit_project(self):
        if field := self.cw.make_selection("Attribute", EDIT_PROJECT_CHOICES):
            new_val = self.cw.get_input(field, EDIT, self.dm.get_card_data(field, self.get_active_card().id)[0])
            self.dm.edit_project(field, new_val, self.get_active_card().id)
        self.update_windows()

    def delete_project(self):
        if self.cw.make_selection("Delete?", ["Yes", "No"], "No") == "Yes":
            self.dm.delete_project(self.get_active_card().id)
            self.up()
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
                    ("macro-blues",     "Custom macropad firmware",     "/home/sean/code/active/c/macro-c.BLUEs/",          "macro-c.BLUEs",      "Active",       "C"),
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
        return [tuple(list(row) + [self.cursor.execute("SELECT COUNT(*) FROM todo WHERE project_id = ? AND deleted = ?;", (row[0], 0,)).fetchone()[0]])
            for row in self.cursor.execute("SELECT * FROM projects WHERE status = ? ORDER BY LOWER(name);", (title,)).fetchall()]

    def pull_todo_data(self, id):
        return self.cursor.execute("SELECT * FROM todo WHERE project_id = ? and deleted = ?", (id, 0)).fetchall()

    def get_card_data(self, column, card_id):
        return self.cursor.execute(f"SELECT {column} FROM projects WHERE id = ?", (card_id,)).fetchone()

    def progress(self, name, current_status):
        self.cursor.execute("UPDATE projects SET status = ? WHERE name = ?", (list(STATUSES.keys())[current_status + 1], name,))
        self.conn.commit()

    def regress(self, name, current_status):
        self.cursor.execute("UPDATE projects SET status = ? WHERE name = ?", (list(STATUSES.keys())[current_status - 1], name,))
        self.conn.commit()

    def add_project(self, name, description, path, file, status, language):
        self.cursor.execute(f"INSERT INTO projects (name, description, path, file, status, language) \
            VALUES (?, ?, ?, ?, ?, ?)", (name, description, path, file, status, language ))
        self.conn.commit()

    def delete_project(self, card_id):
        self.cursor.execute(f"DELETE FROM projects WHERE id = ?", (card_id,))
        self.conn.commit()

    def edit_project(self, new_value_column, new_value, card_id):
        self.cursor.execute(f"UPDATE projects SET {new_value_column} = ? WHERE id = ?", (new_value, card_id,))
        self.conn.commit()

    def add_item(self, new_item, card_id):
        self.cursor.execute("INSERT INTO todo (description, priority, deleted, project_id) VALUES (?, ?, ?, ?)", (new_item, 0, False, card_id))
        self.conn.commit()
        return self.pull_todo_data(card_id)

    def edit_item(self, item_id, new_description, card_id):
        self.cursor.execute("UPDATE todo SET description = ? WHERE id = ? AND project_id = ?", (new_description, item_id, card_id,))
        self.conn.commit()
        return self.pull_todo_data(card_id)

    def delete_item(self, item_id, card_id):
        self.cursor.execute("UPDATE todo SET deleted = ? WHERE id = ?", (1, item_id,))
        self.conn.commit()
        return self.pull_todo_data(card_id)



class TodoManager():
    def __init__(self, active_window, card, todo_list):
        self.active_window = active_window
        self.card = card
        self.todo_list = todo_list

        self.win = None
        self.selected_item = 0

        self.draw()

    def init(self):
        pass

    def draw(self):
        if self.win:
            self.win.erase()
            self.win.refresh()

        longest = max([len(item[1]) for item in self.todo_list]) if len(self.todo_list) > 0 else 20
        self.h, self.w = self.card.todo_count + (4 * Y_PAD) + 1, longest + (4 * X_PAD) + 2
        self.y, self.x = self.card.y, (self.card.x + SECTION_WIDTH - 1) if self.active_window < 2 else self.card.x - longest - (4 * X_PAD) - 2 - 3
        self.win = curses.newwin(self.h, self.w, self.y, self.x)

        draw_box(self.win, c.WHITE)
        self.win.addstr(1, 2, "TODO:", c.WHITE | c.BOLD)
        self.win.addstr(2, 2, "-----", c.WHITE | c.BOLD)
        self.items = ["• " + item[1] for item in self.todo_list if item[3] == 0]
        item_y =  3
        for i, item in enumerate(self.items):
            self.win.addstr(item_y, 4, item, c.INVERT if i == self.selected_item else c.WHITE)
            item_y += 1
        
        self.win.refresh()

    def close(self):
        if self.win:
            self.win.erase()
            self.items = []
            self.win.refresh()
        
    def down(self):
        self.selected_item = min(self.selected_item + 1, self.card.todo_count - 1)
        self.draw()
            
    def up(self):
        self.selected_item = max(self.selected_item - 1, 0)
        self.draw()

    def update_tm(self, new_list):
        self.todo_list = new_list
        self.card.todo_count = len(new_list)
        if self.selected_item >= self.card.todo_count:
            self.up()


class CommandWindow:
    def __init__(self):
        self.h = COMMAND_WINDOW_HEIGHT
        self.w = SCREEN_WIDTH
        self.y = SCREEN_HEIGHT - COMMAND_WINDOW_HEIGHT
        self.x = 0
        self.win = curses.newwin(self.h, self.w, self.y, self.x)
        self.state = ADD
        # self.mode = 

    def set_state(self, state):
        self.state = state

    def init(self):
        self.state = HELP

    def help(self, active_window_index, active_card, in_todo):
        self.win.erase()
        y = Y_PAD
        x = X_PAD * 2
        commands = ["add", "delete", "edit", "quit"] if in_todo else ["add", "delete", "edit", "cd", "nvim", "both", "todo", "progress", "regress", "mode", "quit"]
        for string in commands:
            self.win.addstr(y, x, f"{string[0]}: ", c.CYAN)
            x += 3
            color = c.WHITE
            if not in_todo and \
                ((active_window_index == ABANDONED and string == "regress") \
                or (active_window_index == DONE and string == "progress") \
                or (active_card.file in (None, "") and string == "nvim") \
                or (active_card.path == "" and string == "cd") \
                or (active_card.description in(None, "") and string == "description")):
                color = c.DARK_GREY
            elif in_todo and \
                 (active_card.todo_count <= 0):
                pass
            else:
                color = c.WHITE
            self.win.addstr(y, x, f"{string}", color)
            x += len(string) + 5
        draw_box(self.win, c.WHITE)
        self.win.refresh()

    def make_selection(self, message, choices, default=0):
        y = 1
        x = self.show_message(message, SELECT) + 4
        for i in range(len(choices)):
            self.win.addstr(y, x, f"{i}:", c.CYAN)
            x += 2
            self.win.addstr(y, x, f" {choices[i]}", c.WHITE)
            x += len(choices[i]) + 2 + 3
        selected_number = -1
        while selected_number not in range(0, len(choices)):
            try:
                key = chr(self.win.getch())
                if key == 'q':
                    return None
                selected_number = int(key)
            except ValueError:
                selected_number = -1
        return choices[selected_number]

    def show_message(self, message, state):
        self.win.erase()
        message = message.strip()
        states = ["Adding:", "Changing:", "Deleting:", "Selecting:"]
        mlen = max(len(message) + 3 + 4, len(states[state]))

        draw_box(self.win, c.WHITE)

        message_prompt = f"  {message}    "
        self.win.addstr(1, (1 * X_PAD), message_prompt, c.BRIGHT_YELLOW | c.BOLD)


        self.win.addstr(0, 1, states[state])
        self.win.addch(0, mlen, '┬', c.WHITE)
        self.win.addch(1, mlen, '│', c.WHITE)
        self.win.addch(2, mlen, '┴', c.WHITE)
        return mlen



    def get_input(self, message, state, default="", placeholder_len=0):
        default = default.strip()
        self.win.erase()
        self.win.refresh()
        mlen = self.show_message(message, state)
        if default != "":
            dlen = max(len("Default: "), len(default) + 3 + 4 + 2)
            self.win.addstr(0, mlen + 1, "Default:")
            self.win.addch(0, mlen + dlen, '┬', c.WHITE)
            self.win.addch(1, mlen + dlen, '│', c.WHITE)
            self.win.addch(2, mlen + dlen, '┴', c.WHITE)
            default_prompt = f"   \"{default}\"  "
            self.win.addstr(1, mlen + 1, default_prompt, c.BRIGHT_YELLOW | c.BOLD)
        else:
            dlen = 0

        curses.echo()
        curses.curs_set(1)

        input_pos = (1 * X_PAD) + mlen + dlen + 3
        input, i = [], -1
        self.win.keypad(True)
        while (key := self.win.getch(1, input_pos + i)):
            if key in (10, 13):
                break
            elif key == 27:
                input.clear()
                break
            elif key == curses.KEY_BACKSPACE:
                if len(input) > 0:
                    input.pop(i)
                    i -= 1
                self.win.addstr(1, input_pos + i, ('_' if placeholder_len > 0 else ' '))
                self.win.move(1, input_pos + i - 1)
                self.win.refresh()
                continue
            # elif key == curses.KEY_LEFT:
            #     i -= 1
            #     self.win.move(1, input_pos + i - 1)
            #     self.win.refresh()
            #     continue
            input.append(chr(key))
            i += 1

        finput = "".join(input)
            
        curses.curs_set(0)
        curses.noecho()


        return default if finput == "" else finput
        

class Window:
    def __init__(self, id, height, width, y, x, title, title_pos=2, color=c.WHITE):
        self.id = id
        self.h = height
        self.w = width
        self.y = y
        self.x = x
        self.win = curses.newwin(self.h, self.w, self.y, self.x)
        self.title = title
        self.color = color
        self.title_pos = title_pos
        self.cards = []
        self.card_offset = 0

    def pull(self, dm):
        self.cards = [Card(id=card[0], # id
            height=INACTIVE_CARD_HEIGHT , width=self.w - (2 * X_PAD),y=self.y + Y_PAD, x=self.x + X_PAD,            # UI elements
            name=card[1], path=card[3], description=card[2], file=card[4], language=card[6], todo_count=card[7])    # Card data
                for card in dm.pull_card_data(self.title)]


    def has_cards(self):
        return len(self.cards) > 0

    def update(self, dm, active_window_id, active_card_index, mode=0):

        self.card_offset = 0

        self.pull(dm)

        # TODO: only draw window once
        # draw this Window
        self.draw(active_window_id, mode)

        # TODO: only activate necessary cards (below active one)
        # draw all Cards
        for i, card in enumerate(self.cards):
            if self.id == active_window_id and i == active_card_index:
                card.activate()

            card.draw(self.card_offset, mode)
            self.card_offset += 3 if not card.active else 6


    def draw(self, active_window_id, mode=0):
        style = self.color | c.BOLD if active_window_id == self.id else self.color
        draw_box(self.win, (style if mode != DIM else c.DARK_GREY))
        self.win.addstr(0, self.title_pos, f" {self.title} ({str(len(self.cards))}) ", (c.WHITE | c.BOLD if active_window_id == self.id else style))
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

    def clear(self):
        self.win.erase()

    def draw(self, y_offset, mode):
        self.y += y_offset
        self.win.mvwin(self.y, self.x)
        # self.win.box()

        self.win.addstr(Y_PAD, X_PAD, self.name, self.text_color | c.BOLD)
        self.win.addstr(Y_PAD, self.w - len(self.language) - X_PAD, self.language, self.text_color)

        dark = c.DARK_GREY if mode == BLAND else color_code(self.todo_count, DARK) 
        regular = c.WHITE if mode == BLAND or self.active and self.todo_count == 0 else color_code(self.todo_count, DARK) 

        if self.active:
            draw_box(self.win, regular)
            self.draw_name_border(regular)
            self.win.addstr(3, (self.w // 2) - (len(self.description) // 2), f"{self.description}", c.WHITE)  # description
            self.win.addstr(4, self.w - len("items: ") - 2 - len(str(self.todo_count)), "items: ")            # 'items: '
            self.win.addstr(4, self.w - len(str(self.todo_count)) - 2, f"{self.todo_count}", color_code(self.todo_count, REGULAR))   # todo count
        else:
            draw_box(self.win, dark)

        self.win.refresh()

    def activate(self):
        self.active = True
        self.win.resize(ACTIVE_CARD_HEIGHT, self.w)

    def deactivate(self):
        self.active = False
        self.win.resize(INACTIVE_CARD_HEIGHT, self.w)

    def draw_name_border(self, attributes):
        if self.active:
            self.win.attron(attributes)
            self.win.addch(2, 0, '├')
            self.win.addch(0, len(self.name) + 3, '┬')
            self.win.addch(1, len(self.name) + 3, '│')
            self.win.addch(2, len(self.name) + 3, '┘')
            self.win.addstr(2, 1, '─' * (len(self.name) + 2))
            self.win.attroff(attributes)


def init():
    stdscr.clear()

    curses.curs_set(0)
    curses.noecho()
    curses.set_escdelay(1)
    stdscr.keypad(True)

    stdscr.refresh()

    WINDOWS.extend([
        Window(ABANDONED,  SECTION_HEIGHT, SECTION_WIDTH, 0, ((ABANDONED) * SECTION_WIDTH) + (ABANDONED * X_PAD),   (a := list(STATUSES.keys())[ABANDONED]),color=STATUSES[a]),
        Window(BACKLOG,    SECTION_HEIGHT, SECTION_WIDTH, 0, ((BACKLOG)   * SECTION_WIDTH) + (BACKLOG   * X_PAD),   (b := list(STATUSES.keys())[BACKLOG]),  color=STATUSES[b]),
        Window(ACTIVE,     SECTION_HEIGHT, SECTION_WIDTH, 0, ((ACTIVE)    * SECTION_WIDTH) + (ACTIVE    * X_PAD),   (c := list(STATUSES.keys())[ACTIVE]),   color=STATUSES[c]),
        Window(DONE,       SECTION_HEIGHT, SECTION_WIDTH, 0, ((DONE)      * SECTION_WIDTH) + (DONE      * X_PAD),   (d := list(STATUSES.keys())[DONE]),     color=STATUSES[d])
                    ])

    # Connect to database (or create it if it doesn't exist)
    if sys.argv[0][-3:] == ".py":
        conn = sqlite3.connect(DB_PATH)
    else:
        conn = sqlite3.connect(PROD_DB_PATH)
        # conn = sqlite3.connect(DB_PATH)

    cw = CommandWindow()
    cw.init()
        
    dm = DatabaseManager(conn)
    dm.init()

    sm = StateManager(dm, cw)
    sm.init()

    return sm, dm, cw


def main(stdscr):
    sm, dm, cw = init()

    todo_keymap = {
        "q":        lambda:   sm.quit_todo(),
        "a":        lambda:   sm.add_item(),
        "KEY_UP":   lambda:   sm.tm.up(),
        "KEY_DOWN": lambda:   sm.tm.down(),
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
        "n": lambda:  sm.open_nvim(),
        "b": lambda:  sm.open_both(),
        "t": lambda:  sm.open_todo(),
        "p": lambda:  sm.progress(),
        "r": lambda:  sm.regress(),

        "KEY_LEFT":   lambda:  sm.left(),
        "KEY_RIGHT":  lambda:  sm.right(),
        "KEY_UP":     lambda:  sm.up(),
        "KEY_DOWN":   lambda:  sm.down(),

        "m": lambda:  sm.next_mode(),

        # "": lambda: ,
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

