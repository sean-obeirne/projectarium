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



class StateManager:
    def __init__(self, dm, cw):
        self.dm = dm
        self.cw = cw
        self.tm = None
        self.active_window = 0
        self.active_card = -1
        self.mode = COLORED
        self.in_todo = False
        self.windows = []

    def init(self, windows):
        self.windows = windows
        for window in self.windows:
            window.pull(self.dm)
            if self.active_card == -1 and len(window.cards) > 0:
                self.active_window = window.id
                self.active_card = 0
                self.get_active_card().activate()
                break
        self.update_windows()

    def update_windows(self): # TODO: only update active window and new active window
        for window in self.windows:
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
        self.windows[window_id].update(self.dm, window_id, self.active_card)

    def draw_windows(self):
        for window in self.windows:
            window.draw(self.dm, self.active_window, self.active_card, self.mode)

    def get_cards(self):
        return self.windows[self.active_window].cards

    def get_active_card(self):
        if len(self.get_cards()) > 0:
            return self.windows[self.active_window].cards[self.active_card]
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
        card = self.windows[self.active_window].cards[self.active_card]
        if self.active_window >= 3: return
        self.dm.progress(card.name, self.active_window)
        self.update_windows()
        self.up()
        if len(self.get_cards()) == 0:
            self.right()
        
    def regress(self):
        card = self.windows[self.active_window].cards[self.active_card]
        if self.active_window <= 0: return
        self.dm.regress(card.name, self.active_window)
        self.update_windows()
        self.up()
        if len(self.get_cards()) == 0:
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



