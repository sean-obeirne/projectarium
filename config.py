#
# Author: Sean O'Beirne
# Date: 6-19-2025
# File: state.py
#

#
# Constants for projectarium
#

from ccolors import *

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
Y_PAD                   = 1
X_PAD                   = 2
COMMAND_WINDOW_HEIGHT   = 3
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


COMMAND_STATES      =  [ADD := 0,   DELETE := 1,  EDIT := 2, SELECT := 3]
EDIT_PROJECT_CHOICES   =  ["name", "description", "path", "file", "language"]

WINDOWS = []

MODES = [BLAND := 0, COLORED := 1, DIM := 2]
