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
# import logging
import os
import sys
from typing import Required

# custom curses color module
from ccolors import *       # pyright: ignore[reportWildcardImportFromLibrary]
from cinput import *       # pyright: ignore[reportWildcardImportFromLibrary]



# Configure logging
# logging.basicConfig(filename='debug.log', level=logging.DEBUG, filemode='w', format='%(asctime)s - %(levelname)s - %(message)s')
# log = logging.getLogger(__name__)


# Configure curses
stdscr = curses.initscr()
curses.start_color()
curses.use_default_colors()
init_16_colors()


#Configure windows
HEADER = "Projectarium"
ABANDONED = 0
BACKLOG = 1
ACTIVE = 2
DONE = 3
HELP = 4
STATUSES = {
    "Abandoned":    RED,
    "Backlog":      BLUE,
    "Active":       BRIGHT_YELLOW,
    "Done":         GREEN,
}


# Assign other variables
PROD_DB_PATH = "/home/sean/.local/share/projectarium/.projectarium.db"
DB_PATH = ".projectarium.db"
TERMINAL_PREFIX = "gnome-terminal --maximize --working-directory="
NEOVIM_PREFIX = "nvim "
TMUX_PREFIX = "tmux new-session -A -s "


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
TODO_COLORS = [(NO_TODO_ITEMS, REGULAR, DIM_WHITE), (LOW_TODO_ITEMS, REGULAR, GREEN), (MEDIUM_TODO_ITEMS, REGULAR, BRIGHT_YELLOW), (MAX_TODO_ITEMS, REGULAR, RED),
               (NO_TODO_ITEMS, DARK, GUTTER), (LOW_TODO_ITEMS, DARK, LIGHT_GREEN), (MEDIUM_TODO_ITEMS, DARK, YELLOW), (MAX_TODO_ITEMS, DARK, LIGHT_RED)
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

        # Implicit, no explicit shortcut mapping
        # commands = ["add", "delete", "edit", "quit"] if self.in_todo else ["add", "delete", "edit", "cd", "nvim", "both", "todo", "progress", "regress", "mode", "quit"]

        # Explicit shortcut mapping
        if self.in_todo:
            commands = [("a", "add"), ("e", "delete"), ("e", "edit"), ("q", "quit")] 
        else:
            commands = [("a", "add"), ("d", "delete"), ("e", "edit"), ("c", "cd"), ("n", "nvim"), ("m", "tmux"),
                        ("b", "both"), ("t", "todo"), ("p", "progress"), ("r", "regress"), ("v", "view"), ("q", "quit")]
        self.cw.help(commands)

    def update_window(self, window_id=None):
        window_id = self.active_window if window_id is None else window_id
        WINDOWS[window_id].update(self.dm, window_id, self.active_card)

    def get_cards(self):
        return WINDOWS[self.active_window].cards

    def get_active_card(self):
        if len(self.get_cards()) > 0:
            return WINDOWS[self.active_window].cards[self.active_card]
        else:
            return Card(-1, 0, 0, 0, 0, "", "", "", "", 0, "") # dummy card to fool linter
    # def __init__(self, id, height, width, y, x, name, path, description="", file="", priority=0, language="", todo_count=0):

    def open_dir(self, quit=False):
        os.system(f"{TERMINAL_PREFIX}{self.get_active_card().path}")
        if quit: exit(0)

    def open_nvim(self, quit=False):
        os.system(f"{TERMINAL_PREFIX}{self.get_active_card().path} -- bash -c \'{NEOVIM_PREFIX + self.get_active_card().file}\'") if self.get_active_card().file != "" else "",         # pyright: ignore[reportUnusedExpression]
        if quit: exit(0)

    def open_tmux(self, quit=False):
        session_name = self.get_active_card().name.lower().replace(" ", "_").replace("-", "_")
        os.system(f"{TERMINAL_PREFIX}{self.get_active_card().path} -- bash -c \'{TMUX_PREFIX} {session_name} -c {self.get_active_card().path}\' &> /dev/null")
        if quit: exit(0)


    def open_both(self, quit=False):
        self.open_dir()
        self.open_nvim()
        if quit: exit(0)

    def set_mode(self, new_mode):
        self.mode = new_mode
        self.update_windows()

    def next_mode(self):
        self.mode = (self.mode + (2 if self.mode == 1 else 1)) % len(MODES)
        self.update_windows()

    def open_todo(self):
        self.tm = TodoManager(self.active_window, self.get_active_card(), self.dm.pull_todo_data(self.get_active_card().id))
        self.in_todo = True
        # self.cw.help(self.active_window, self.get_active_card(), self.in_todo)
        self.set_mode(DIM)
        self.update_windows()
        self.tm.draw()

    def quit_todo(self):
        if self.tm: self.tm.close()
        self.update_windows()
        self.in_todo = False
        self.set_mode(COLORED)
        # self.cw.help(self.active_window, self.get_active_card(), self.in_todo)

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

    def increment_priority(self):
        card = WINDOWS[self.active_window].cards[self.active_card]
        if card.priority < 99:
            self.dm.increment_priority(card.name, card.priority)
            self.update_windows()

    def decrement_priority(self):
        card = WINDOWS[self.active_window].cards[self.active_card]
        if card.priority > 0:
            self.dm.decrement_priority(card.name, card.priority)
            self.update_windows()
        
    def add_item(self):
        if self.tm:
            self.tm.update_tm(self.dm.add_item(self.cw.get_input("New todo item", required=True), self.get_active_card().id))
            self.update_windows()
            self.tm.draw()

    def edit_item(self):
        if self.tm and self.get_active_card().todo_count > 0:
            new_description = self.cw.get_input("Description", default=self.tm.todo_list[self.tm.selected_item][1], required=True)
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
        name = self.cw.get_input("Name", required=True)
        description = self.cw.get_input("Description")
        path = self.cw.get_input("Path", input_type="path", required=True)
        file = self.cw.get_input("File", input_type="path")
        language = self.cw.get_input("Language")
        self.dm.add_project(name, description, path, file, "Backlog", language)
        self.update_windows()

    def edit_project(self):
        if field := self.cw.make_selection("Attribute", EDIT_PROJECT_CHOICES):
            new_val = self.cw.get_input(field, default=self.dm.get_card_data(field, self.get_active_card().id)[0])
            self.dm.edit_project(field, new_val, self.get_active_card().id)
        self.update_windows()

    def delete_project(self):
        if self.cw.make_selection("Delete?", ["Yes", "No"], default="No", required=True) == "Yes":
            self.dm.delete_project(self.get_active_card().id)
            self.up()
        self.update_windows()



class DatabaseManager:
    def __init__(self, conn,):
        self.conn = conn
        self.cursor = conn.cursor()
        self.init()

    def init(self):
        # Create the 'projects' table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT CHECK(LENGTH(description) <= 29),
                path TEXT NOT NULL,
                file TEXT,
                priority INTEGER DEFAULT 0,
                status TEXT NOT NULL,
                language TEXT
            );
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
            );
        ''')

        # self.cursor.execute("ALTER TABLE projects ADD COLUMN priority INTEGER DEFAULT 0;")

        self.conn.commit()

        if DB_PATH == ".projectarium.db":
            self.init_populate()

    def init_populate(self):
        if DB_PATH == ".projectarium.db":
            # Optional: Insert some default data only if the database is empty
            self.cursor.execute("SELECT COUNT(*) FROM projects")
            if self.cursor.fetchone()[0] == 0:
                default_projects = [
                    ("WotR",            "Wizards of the Rift",          "/home/sean/code/paused/godot/Wizards-of-the-Rift/","",                 0,  "Abandoned",  "Godot"),
                    ("LearnScape",      "General learning visualizer",  "/home/sean/code/paused/LearnScape/",               "learnscape.py",    0,  "Abandoned",  "Python"),
                    ("ROMs",            "ROM emulation optimization",   "/home/sean/code/future/ROMs/",                     "",                 0,  "Backlog",      "C"),
                    ("goverse",         "Go VCS application",           "/home/sean/code/active/go/goverse/",               "cli/main.go",      0,  "Active",       "Go"),
                    ("projectarium",    "Project progress tracker",     "/home/sean/code/active/python/projectarium/",      "projectarium.py",  0,  "Active",       "Python"),
                    ("snr",             "Search and replace plugin",    "/home/sean/.config/nvim/lua/snr/",                 "init.lua",         0,  "Active",       "Lua"),
                    ("todua",           "Todo list for Neovim",         "/home/sean/.config/nvim/lua/todua/",               "init.lua",         0,  "Active",       "Lua"),
                    ("macro-blues",     "Custom macropad firmware",     "/home/sean/code/active/c/macro-c.BLUEs/",          "macro-c.BLUEs",    0,  "Active",       "C"),
                    ("leetcode",        "Coding interview practice",    "/home/sean/code/paused/leetcode/",                 "",                 0,  "Active",       "Python"),
                    ("TestTaker",       "ChatGPT->Python test maker",   "/home/sean/code/paused/TestTaker/",                "testtaker.py",     0,  "Active",       "Python"),
                    ("Mission-Uplink",  "TFG Mission Uplink",           "/home/sean/code/tfg/Mission-Uplink/",              "README.md",        0,  "Active",       "Go,C"),
                    ("Sorter",          "Sorting algoithm visualizer",  "/home/sean/code/done/Sorter/",                     "sorter.py",        0,  "Done",         "Python"),
                    ("landing-page",    "Cute application launcher",    "/home/sean/code/done/landing-page/",               "landing-page.py",  0,  "Done",         "Python"),
                    ####################"   valid description length  "###################################################################################################
                ]
                self.cursor.executemany('''
                    INSERT INTO projects (name, description, path, file, priority, status, language)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
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
            for row in self.cursor.execute("SELECT * FROM projects WHERE status = ? ORDER BY priority DESC, LOWER(name);", (title,)).fetchall()]

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

    def increment_priority(self, name, current_priority):
        self.cursor.execute("UPDATE projects SET priority = ? WHERE name = ?", (current_priority + 1, name,))
        self.conn.commit()

    def decrement_priority(self, name, current_priority):
        self.cursor.execute("UPDATE projects SET priority = ? WHERE name = ?", (current_priority - 1, name,))
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

        draw_box(self.win, WHITE)
        self.win.addstr(1, 2, "TODO:", WHITE | BOLD)
        self.win.addstr(2, 2, "-----", WHITE | BOLD)
        self.items = ["• " + item[1] for item in self.todo_list if item[3] == 0]
        item_y =  3
        for i, item in enumerate(self.items):
            self.win.addstr(item_y, 4, item, INVERT if i == self.selected_item else WHITE)
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


class Window:
    def __init__(self, id, height, width, y, x, title, title_pos=2, color=WHITE):
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
            name=card[1], path=card[3], description=card[2], file=card[4], priority=card[5], language=card[7], todo_count=card[8])    # Card data
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
        style = self.color | BOLD if active_window_id == self.id else self.color
        draw_box(self.win, (style if mode != DIM else DARK_GREY))
        self.win.addstr(0, self.title_pos, f" {self.title} ({str(len(self.cards))}) ", (WHITE | BOLD if active_window_id == self.id else style))
        self.win.refresh()


class Card():
    def __init__(self, id, height, width, y, x, name, path, description="", file="", priority=0, language="", todo_count=0):
        self.id = id
        self.h = height
        self.w = width
        self.y = y
        self.x = x
        self.win = curses.newwin(self.h, self.w, self.y, self.x)
        self.name = name
        self.path = path
        self.file = file
        self.priority = priority
        self.description = description
        self.language = language
        self.todo_count = todo_count
        self.active = False
        self.text_color = WHITE

    def clear(self):
        self.win.erase()

    def draw(self, y_offset, mode):
        self.y += y_offset
        self.win.mvwin(self.y, self.x)
        # self.win.box()

        self.win.addstr(Y_PAD, X_PAD, self.name, self.text_color | BOLD)
        self.win.addstr(Y_PAD, self.w - len(self.language) - X_PAD, self.language, self.text_color)

        dark = DARK_GREY if mode == BLAND else color_code(self.todo_count, DARK) 
        regular = WHITE if mode == BLAND or self.active and self.todo_count == 0 else color_code(self.todo_count, DARK) 

        if self.active:
            draw_box(self.win, regular)
            self.draw_name_border(regular)
            self.win.addstr(3, (self.w // 2) - (len(self.description) // 2), f"{self.description}", WHITE)  # description
            self.win.addstr(4, self.w - len("items: ") - 2 - len(str(self.todo_count)), "items: ")            # 'items: '
            # self.win.addstr(4, self.w - len("items: ") - 2 - len(str(self.todo_count)), "items: ")            # 'items: '
            self.win.addstr(4, 2, "priority: ")
            self.win.addstr(4, len("priority: ") + 2, f"{self.priority}")
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
        
    dm = DatabaseManager(conn)
    dm.init()

    sm = StateManager(dm, cw)
    sm.init()

    return sm


def main(stdscr):
    sm = init()

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

