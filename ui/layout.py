#
# Author: Sean O'Beirne
# Date: 6-19-2025
# File: layout.py
#

#
# Windows and Cards for TUI Kanban board
#

from config import *

import curses

def draw_box(window, attributes):
    window.attron(attributes)
    window.box()
    window.attroff(attributes)

class Window:
    def __init__(self, id, win, title, color=WHITE):
        self.id = id
        self.win = win
        self.title = title
        self.color = color
        self.cards = []
        self.card_offset = 0

        self.h, self.w = self.win.getmaxyx()
        self.y = 0
        self.x = STATUSES[self.title][0] * self.w

    def __str__(self):
        return f"Window(id={self.id}, title='{self.title}', color={self.color}, cards={len(self.cards)})"

    def has_cards(self):
        return len(self.cards) > 0

    def add_card(self, project):
        new_y = self.y + Y_PAD + self.card_offset
        new_x = self.x + (X_PAD * self.id) + X_PAD
        card = Card.new_card(project, new_y, new_x, INACTIVE_CARD_HEIGHT, self.w - (2 * X_PAD))
        log.info(f"Adding card {card} to window {self.id} at position ({new_y}, {new_x})")
        self.cards.append(card)
        self.card_offset += INACTIVE_CARD_HEIGHT

    def draw_window(self, active_window_id, active_card_id, mode=0):
        style = self.color | BOLD if active_window_id == self.id else self.color
        draw_box(self.win, (style if mode != DIM else DARK_GREY))
        self.win.addstr(0, X_PAD, f" {self.title} ({str(len(self.cards))}) ", (WHITE | BOLD if active_window_id == self.id else style))
        self.win.refresh()

        log.info(f"Length of cards in window {self.id}: {len(self.cards)}, cards: {[str(card) for card in self.cards]}")
        self.card_offset = 0
        for i, card in enumerate(self.cards):
            active = (self.id == active_window_id and i == active_card_id)
            log.info(f"Drawing card {card} at offset {self.card_offset} in window {self.id}, active: {active}")
            card.win.mvwin(self.y + self.card_offset + Y_PAD, self.x + X_PAD + (self.id * X_PAD))
            card.win.resize(ACTIVE_CARD_HEIGHT, self.w - 2*X_PAD)
            card.draw_card(mode, active)
            self.card_offset += ACTIVE_CARD_HEIGHT if active else INACTIVE_CARD_HEIGHT


class Card():
    def __init__(self, id, win, name, path, description="", file="", priority=0, status="", language="", todo_count=0):
        self.id = id
        self.win = win
        self.h, self.w = win.getmaxyx()
        self.y, self.x = win.getbegyx()
        self.name = name
        self.path = path
        self.file = file
        self.priority = priority
        self.description = description
        self.status = status
        self.language = language
        self.todo_count = todo_count
        self.active = False
        self.text_color = WHITE

    def __str__(self):
        return f"Card(id={self.id}, name='{self.name}', status={self.status})"

    @classmethod
    def from_project(cls, project):
        return cls(
            project.id,
            curses.newwin(INACTIVE_CARD_HEIGHT, 0, 0, 0),  # Placeholder for win, will be given later
            project.name,
            project.path,
            project.description,
            project.file,
            project.priority,
            project.status,
            project.language,
            project.todo_count
        )

    @classmethod
    def new_card(cls, project, y, x, h, w):
        return cls(
            project.id,
            curses.newwin(h, w, y, x),
            project.name,
            project.path,
            project.description,
            project.file,
            project.priority,
            project.status,
            project.language,
            project.todo_count
        )

    def clear(self):
        self.win.erase()

    def draw_card(self, mode, active=False):
        # self.activate()
        # self.y += y_offset
        # self.win = curses.newwin(height, width - 2 * X_PAD, self.y, self.x + X_PAD + x_offset)

        self.win.addstr(Y_PAD, X_PAD, self.name, self.text_color | BOLD)
        # self.win.addstr(Y_PAD, self.w - len(self.language) - X_PAD, self.language, self.text_color)

        dark = DARK_GREY if mode == BLAND else color_code(self.todo_count, DARK) 
        regular = WHITE if mode == BLAND or active and self.todo_count == 0 else color_code(self.todo_count, DARK) 

        if active:
            self.win.resize(ACTIVE_CARD_HEIGHT, self.w)
            draw_box(self.win, regular)
            self.draw_name_border(regular)
            self.win.addstr(3, (self.w // 2) - (len(self.description) // 2), f"{self.description}", WHITE)  # description
            self.win.addstr(4, self.w - len("items: ") - 2 - len(str(self.todo_count)), "items: ")            # 'items: '
            self.win.addstr(4, self.w - len("items: ") - 2 - len(str(self.todo_count)), "items: ")            # 'items: '
            self.win.addstr(4, 2, "priority: ")
            self.win.addstr(4, len("priority: ") + 2, f"{self.priority}")
            self.win.addstr(4, self.w - len(str(self.todo_count)) - 2, f"{self.todo_count}", color_code(self.todo_count, REGULAR))   # todo count
        else:
            self.win.resize(INACTIVE_CARD_HEIGHT, self.w)
            draw_box(self.win, dark)

        self.win.refresh()

    def draw_name_border(self, attributes):
        if self.active:
            self.win.attron(attributes)
            self.win.addch(2, 0, '├')
            self.win.addch(0, len(self.name) + 3, '┬')
            self.win.addch(1, len(self.name) + 3, '│')
            self.win.addch(2, len(self.name) + 3, '┘')
            self.win.addstr(2, 1, '─' * (len(self.name) + 2))
            self.win.attroff(attributes)


class TodoList():
    def __init__(self, active_window, card, todo_list):
        self.active_window = active_window
        self.card = card
        self.todo_list = todo_list

        self.win = None
        self.selected_item = 0

        self.draw_todo()

    def init(self):
        pass

    def draw_todo(self):
        if self.win:
            self.win.erase()
            self.win.refresh()

        longest = max([len(item[1]) for item in self.todo_list]) if len(self.todo_list) > 0 else 20
        # log.info(f"Longest todo item length: {longest}")
        self.h = self.card.todo_count + (4 * Y_PAD) + 1
        self.w = longest + (4 * X_PAD) + 2
        self.y, self.x = self.card.win.getbegyx()
        if self.active_window < 2:
            self.x += self.card.win.getmaxyx()[1] + 1 + X_PAD
        else:
            self.x -= longest
            self.x -= (4 * X_PAD) + 2
            self.x -= 3
        # self.x = (self.card.x + 10 - 1) if self.active_window < 2 else max(self.card.x - longest - (4 * X_PAD) - 2 - 3, 0)
        # log.info(f"TodoList initialized with card at ({self.card.x}, {self.card.y}) and active window {self.active_window}.")
        # log.info(f"Drawing todo list at ({self.x}, {self.y}) with size ({self.w}, {self.h})")
        self.win = curses.newwin(self.h, self.w, self.y, self.x)

        draw_box(self.win, PURPLE)
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
        self.draw_todo()
            
    def up(self):
        self.selected_item = max(self.selected_item - 1, 0)
        self.draw_todo()

    def update_tm(self, new_list):
        self.todo_list = new_list
        self.card.todo_count = len(new_list)
        if self.selected_item >= self.card.todo_count:
            self.up()


