#
# Author: Sean O'Beirne
# Date: 6-19-2025
# File: layout.py
#

#
# Windows and Cards for TUI Kanban board
#

from ccolors import *
from config import *

def draw_box(window, attributes):
    window.attron(attributes)
    window.box()
    window.attroff(attributes)

class Window:
    def __init__(self, id, win, title, title_pos=2, color=WHITE):
        self.id = id
        self.win = win
        # self.h = height
        # self.w = width
        # self.y = y
        # self.x = x
        # self.win = curses.newwin(self.h, self.w, self.y, self.x)
        self.title = title
        self.color = color
        self.title_pos = title_pos
        self.cards = []
        self.card_offset = 0

    def pull(self, dm):
        self.cards = []
        # self.cards = [Card(id=card[0], # id
        #     height=INACTIVE_CARD_HEIGHT , width=self.w - (2 * X_PAD),y=self.y + Y_PAD, x=self.x + X_PAD,            # UI elements
        #     name=card[1], path=card[3], description=card[2], file=card[4], priority=card[7], language=card[6], todo_count=card[8])    # Card data
        #         for card in dm.pull_card_data(self.title)]

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

