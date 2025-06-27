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
    def __init__(self, id, win, title, title_pos=2, color=WHITE, cards=[]):
        self.id = id
        self.win = win
        # self.h = height
        # self.w = width
        self.title = title
        self.color = color
        self.title_pos = title_pos
        self.cards = cards
        self.card_offset = 0

        self.h, self.w = self.win.getmaxyx()
        self.y = 0
        self.x = STATUSES[self.title][0] * self.w
        # self.x = x
        # self.win = curses.newwin(self.h, self.w, self.y, self.x)
        

    # def create_card(self, id, name, path="", description="", file="", priority=0, language="", todo_count=0):
    #     card_win = curses.newwin(INACTIVE_CARD_HEIGHT, self.w - (2 * X_PAD), self.y + Y_PAD, self.x + X_PAD)
    #     self.cards.append(Card(id, card_win, name, path,
    #         description, file, priority, language, todo_count))  # Card data

    def add_card(self, card):
        card.assign(curses.newwin(INACTIVE_CARD_HEIGHT, self.w - (2 * X_PAD), self.y + Y_PAD, self.x + X_PAD))
        self.cards.append(card)

    def has_cards(self):
        return len(self.cards) > 0

    def update(self, active_window_id, active_card_index, mode=0):
        self.card_offset = 0

        # TODO: only draw window once
        # draw this Window
        self.draw(active_window_id, mode)

        # TODO: only activate necessary cards (below active one)
        # draw all Cards
        for i, card in enumerate(self.cards):
            if self.id == active_window_id and i == active_card_index:
                card.activate()

            card.draw(self.card_offset + Y_PAD, self.x + (self.id * X_PAD), mode)
            self.card_offset += 3 if not card.active else 6


    def draw(self, active_window_id, mode=0):
        style = self.color | BOLD if active_window_id == self.id else self.color
        draw_box(self.win, (style if mode != DIM else DARK_GREY))
        self.win.addstr(0, self.title_pos, f" {self.title} ({str(len(self.cards))}) ", (WHITE | BOLD if active_window_id == self.id else style))
        self.win.refresh()


class Card():
    def __init__(self, id, win, name, path, description="", file="", priority=0, status="", language="", todo_count=0):
        self.id = id
        # self.h = height
        # self.w = width
        # self.y = y
        # self.x = x
        self.win = win
        self.h, self.w = win.getmaxyx()
        self.y, self.x = win.getyx()
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

    @classmethod
    def from_project(cls, project):
        return cls(
            project.id,
            curses.newwin(INACTIVE_CARD_HEIGHT, 0, 0, 0),  # Placeholder window, will be resized later
            project.name,
            project.path,
            project.description,
            project.file,
            project.priority,
            project.status,
            project.language,
            project.todo_count
        )

    def assign(self, win):
        self.win = win
        self.h, self.w = win.getmaxyx()
        self.y, self.x = win.getyx()
        # self.win.resize(INACTIVE_CARD_HEIGHT, self.w)

    def clear(self):
        self.win.erase()

    def draw(self, y_offset, x_offset, mode):
        log.info(f"Drawing card: {self.name} at offset {y_offset}")
        self.y += y_offset
        self.win.mvwin(self.y, self.x + X_PAD + x_offset)
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

