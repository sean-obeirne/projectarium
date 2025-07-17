#
# Author: Sean O'Beirne
# Date: 6-21-2025
# File: db.py
#

#
# Tracks te database of projectarium
#

from config import *
from objects import Project, TodoItem

import sqlite3



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


    def pull_projects(self, status_filter=""):
        if status_filter:
            status_filter = f"WHERE status = '{status_filter}'"
        entries = self.cursor.execute(f"SELECT * FROM projects {status_filter} ORDER BY priority DESC, LOWER(name);", ()).fetchall()
        projects = []
        for entry in entries:
            pid, name, description, path, file, priority, status, language = entry
            
            todo_count = self.cursor.execute("SELECT COUNT(*) FROM todo WHERE project_id = ? AND deleted = ?", (pid, 0)).fetchone()[0]

            projects.append(Project(
                id=pid,
                name=name,
                description=description or "",
                path=path,
                file=file or "",
                priority=priority,
                status=status,
                language=language or "",
                todo_count=todo_count
            ))
            # log.debug(f"Pulled project: {name} with status: {status} and todo count: {todo_count}")

        return projects

    def pull_card_data(self, title):
        # log.info(f"Pulling card data for status: {title}")
        db_cards = self.cursor.execute("SELECT * FROM projects WHERE status = ? ORDER BY priority DESC, LOWER(name);", (title,)).fetchall()
        # get cards, then append to the end of the query result the number of tasks the card has
        # return [tuple(list(row) + [self.cursor.execute("SELECT COUNT(*) FROM todo WHERE project_id = ? AND deleted = ?;", (row[0], 0,)).fetchone()[0]])
            # for 

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


