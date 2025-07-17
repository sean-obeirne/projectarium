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

STATUS_NAMES = ["Abandoned", "Backlog", "Active", "Done"]


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

    def init(self):
        self.projects = self.dm.pull_projects()
        # self.get_active_window_projects()

    def get_projects(self) -> list[Card]:
        return [Card.from_project(project) for project in self.projects]

    def get_projects_by_status(self, status) -> list[Card]:
        return [Card.from_project(project) for project in self.projects if project.status == status]

    def draw_cw(self): # TODO: only update active window and new active window
        # Explicit shortcut mapping
        if self.in_todo:
            commands = [("a", "add"), ("e", "delete"), ("e", "edit"), ("q", "quit")] 
        else:
            commands = [("a", "add"), ("d", "delete"), ("e", "edit"), ("c", "cd"), ("n", "nvim"), ("m", "tmux"),
                        ("b", "both"), ("t", "todo"), ("p", "progress"), ("r", "regress"), ("v", "view"), ("q", "quit")]
        self.cw.help(commands)

        # Implicit shortcut mapping example:
        # commands = ["add", "delete", "edit", "quit"] if self.in_todo else ["add", "delete", "edit", "cd", "nvim", "both", "todo", "progress", "regress", "mode", "quit"]


    def get_active_window(self) -> str:
        return STATUS_NAMES[self.active_window]

    def get_active_card(self) -> Project:
        return self.get_active_window_projects()[self.active_card]

    def get_active_window_projects(self) -> list[Project]:
        return [project for project in self.projects if project.status == STATUS_NAMES[self.active_window]]

###########################
### USERSPACE FUNCTIONS ###
###########################

    def open_dir(self, quit=False):
        os.system(f"{TERMINAL_PREFIX}{self.get_active_card().path}")
        if quit: exit(0)

    def open_nvim(self, quit=False):
        log.info(f"Opening Neovim for card: {self.get_active_card().name} in window {self.active_window}")
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
        

    def next_mode(self):
        self.mode = (self.mode + (2 if self.mode == 1 else 1)) % len(MODES)
        

    def open_todo(self):
        # log.info(f"Opening todo for card: {self.get_active_card().name} in window {self.active_window}")
        self.tm = TodoList(self.active_window, self.get_active_card(), self.dm.pull_todo_data(self.get_active_card().id))
        self.in_todo = True
        # self.cw.help(self.active_window, self.get_active_card(), self.in_todo)
        self.set_mode(DIM)
        
        self.tm.draw_todo()

    def quit_todo(self):
        if self.tm: self.tm.close()
        
        self.in_todo = False
        self.set_mode(COLORED)
        # self.cw.help(self.active_window, self.get_active_card(), self.in_todo)

    def hide_todo(self):
        if self.tm: self.tm.close()


    def up(self):
        if self.active_card > 0:
            self.active_card -= 1

    def down(self):
        if self.active_card < len(self.get_active_window_projects()) - 1:
            self.active_card += 1

    def right(self):
        # log.info(f"Active window: {self.active_window}, Total windows: {len(self.windows)}")
        if self.active_window < 3:
            self.active_window += 1

    def left(self):
        if self.active_window > 0:
            self.active_window -= 1


    def progress(self):
        card = self.windows[self.active_window].cards[self.active_card]
        if self.active_window >= 3: return
        self.dm.progress(card.name, self.active_window)
        
        self.up()
        if len(self.get_active_window_cards()) == 0:
            self.right()
        
    def regress(self):
        card = self.windows[self.active_window].cards[self.active_card]
        if self.active_window <= 0: return
        self.dm.regress(card.name, self.active_window)
        
        self.up()
        if len(self.get_active_window_cards()) == 0:
            self.left()

    def increment_priority(self):
        card = self.windows[self.active_window].cards[self.active_card]
        if card.priority < 99:
            self.dm.increment_priority(card.name, card.priority)
            

    def decrement_priority(self):
        card = self.windows[self.active_window].cards[self.active_card]
        if card.priority > 0:
            self.dm.decrement_priority(card.name, card.priority)
            
        
    def add_item(self):
        if self.tm:
            self.tm.update_tm(self.dm.add_item(self.cw.get_input("New todo item", required=True), self.get_active_card().id))
            
            self.tm.draw_todo()

    def edit_item(self):
        if self.tm and self.get_active_card().todo_count > 0:
            new_description = self.cw.get_input("Description", default=self.tm.todo_list[self.tm.selected_item][1], required=True)
            todo_id = self.tm.todo_list[self.tm.selected_item][0]
            self.tm.update_tm(self.dm.edit_item(todo_id, new_description, self.get_active_card().id))
            
            self.tm.draw_todo()

    def delete_item(self):
        if self.tm and self.get_active_card().todo_count > 0:
            self.tm.update_tm(self.dm.delete_item(self.tm.todo_list[self.tm.selected_item][0], self.get_active_card().id))
            
            self.tm.draw_todo()

    def add_project(self):
        name = self.cw.get_input("Name", required=True)
        description = self.cw.get_input("Description")
        path = self.cw.get_input("Path", input_type="path", required=True)
        file = self.cw.get_input("File", input_type="path")
        language = self.cw.get_input("Language")
        self.dm.add_project(name, description, path, file, "Backlog", language)
        

    def edit_project(self):
        if field := self.cw.make_selection("Attribute", EDIT_PROJECT_CHOICES):
            new_val = self.cw.get_input(field, default=self.dm.get_card_data(field, self.get_active_card().id)[0])
            self.dm.edit_project(field, new_val, self.get_active_card().id)
        

    def delete_project(self):
        if self.cw.make_selection("Delete?", ["Yes", "No"], default="No", required=True) == "Yes":
            self.dm.delete_project(self.get_active_card().id)
            self.up()
        


