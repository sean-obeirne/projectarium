#
# Author: Sean O'Beirne
# Date: 6-19-2025
# File: state.py
#

#
# Tracks te state of projectarium
#

import os

from config import *
from db import DatabaseManager
from objects import Project, TodoItem

from ui.layout import Window, Card, TodoList

import curses


class StateManager:
    def __init__(self, dm, cw):
        self.dm = dm
        self.cw = cw
        self.tm = None
        self.active_window = 0
        self.active_card = 0
        self.mode = COLORED
        self.in_todo = False
        self.projects = []
        self.windows = []

    def init(self, windows):
        self.windows = [windows[i] for i in range(len(windows))]
        self.projects = self.dm.pull_projects()
        log.info(f"Projects pulled: {len(self.projects)}")

        self.update_windows()
        for window in self.windows:
            for project in self.projects:
                if project.status == window.title:
                    log.info(f"Adding cards to window {window.title}, project {project.name}")
                    window.add_card(project)
            if self.active_card == -1 and len(window.cards) > 0:
                self.active_window = window.id
                self.active_card = 0
                self.get_active_card().activate()
                # break

    def get_projects(self) -> list[Card]:
        return [Card.from_project(project) for project in self.dm.pull_projects()]

    def get_projects_by_status(self, status) -> list[Card]:
        return [Card.from_project(project) for project in self.dm.pull_projects() if project.status == status]

    def update_windows(self): # TODO: only update active window and new active window
        for window in self.windows:
            log.info(f"Updating window {window.title} with {len(self.get_projects_by_status(window.title))} projects")
            window.update_window(self.get_projects_by_status(window.title), self.active_window, self.active_card, mode=self.mode)

        # Implicit, no explicit shortcut mapping
        # commands = ["add", "delete", "edit", "quit"] if self.in_todo else ["add", "delete", "edit", "cd", "nvim", "both", "todo", "progress", "regress", "mode", "quit"]

        # Explicit shortcut mapping
        if self.in_todo:
            commands = [("a", "add"), ("e", "delete"), ("e", "edit"), ("q", "quit")] 
        else:
            commands = [("a", "add"), ("d", "delete"), ("e", "edit"), ("c", "cd"), ("n", "nvim"), ("m", "tmux"),
                        ("b", "both"), ("t", "todo"), ("p", "progress"), ("r", "regress"), ("v", "view"), ("q", "quit")]
        self.cw.help(commands)

    def get_active_window_cards(self):
        return self.windows[self.active_window].cards

    def get_active_card(self):
        if len(self.get_active_window_cards()) > 0:
            return self.windows[self.active_window].cards[self.active_card]
        else:
            log.warning("No active card found, returning dummy card")
            return Card(-1, curses.newwin(0, 0, 0, 0), "No active card", "", "", "", 0, "", "", 0) # pyright: ignore[reportArgumentType]


###########################
### USERSPACE FUNCTIONS ###
###########################

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
        # log.info(f"Opening todo for card: {self.get_active_card().name} in window {self.active_window}")
        self.tm = TodoList(self.active_window, self.get_active_card(), self.dm.pull_todo_data(self.get_active_card().id))
        self.in_todo = True
        # self.cw.help(self.active_window, self.get_active_card(), self.in_todo)
        self.set_mode(DIM)
        self.update_windows()
        self.tm.draw_todo()

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
        if self.active_card < len(self.get_active_window_cards()) - 1:
            self.navigate(lambda: setattr(self, "active_card", self.active_card + 1))
                          # lambda: min(self.active_card + 1, max(len(self.get_active_window_cards()) - 1, 0)))

    def right(self):
        if self.active_window < 3:
            self.navigate(lambda: setattr(self, "active_window", self.active_window + 1),
                          lambda: min(self.active_card, max(len(self.get_active_window_cards()) - 1, 0)))

    def left(self):
        if self.active_window > 0:
            self.navigate(lambda: setattr(self, "active_window", self.active_window - 1), 
                          lambda: min(self.active_card, max(len(self.get_active_window_cards()) - 1, 0)))


    def progress(self):
        card = self.windows[self.active_window].cards[self.active_card]
        if self.active_window >= 3: return
        self.dm.progress(card.name, self.active_window)
        self.update_windows()
        self.up()
        if len(self.get_active_window_cards()) == 0:
            self.right()
        
    def regress(self):
        card = self.windows[self.active_window].cards[self.active_card]
        if self.active_window <= 0: return
        self.dm.regress(card.name, self.active_window)
        self.update_windows()
        self.up()
        if len(self.get_active_window_cards()) == 0:
            self.left()

    def increment_priority(self):
        card = self.windows[self.active_window].cards[self.active_card]
        if card.priority < 99:
            self.dm.increment_priority(card.name, card.priority)
            self.update_windows()

    def decrement_priority(self):
        card = self.windows[self.active_window].cards[self.active_card]
        if card.priority > 0:
            self.dm.decrement_priority(card.name, card.priority)
            self.update_windows()
        
    def add_item(self):
        if self.tm:
            self.tm.update_tm(self.dm.add_item(self.cw.get_input("New todo item", required=True), self.get_active_card().id))
            self.update_windows()
            self.tm.draw_todo()

    def edit_item(self):
        if self.tm and self.get_active_card().todo_count > 0:
            new_description = self.cw.get_input("Description", default=self.tm.todo_list[self.tm.selected_item][1], required=True)
            todo_id = self.tm.todo_list[self.tm.selected_item][0]
            self.tm.update_tm(self.dm.edit_item(todo_id, new_description, self.get_active_card().id))
            self.update_windows()
            self.tm.draw_todo()

    def delete_item(self):
        if self.tm and self.get_active_card().todo_count > 0:
            self.tm.update_tm(self.dm.delete_item(self.tm.todo_list[self.tm.selected_item][0], self.get_active_card().id))
            self.update_windows()
            self.tm.draw_todo()

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


