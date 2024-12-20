import curses
# Placeholder declarations for constants
INVERT = None
RED = None
GREEN = None
ORANGE = None
BLUE = None
GUTTER = None
CYAN = None
WHITE = None
DARK_GREY = None
LIGHT_RED = None
LIGHT_GREEN = None
YELLOW = None
LIGHT_BLUE = None
PURPLE = None
BRIGHT_YELLOW = None
DIM_WHITE = None

NORMAL = curses.A_NORMAL
BOLD = curses.A_BOLD
ITALIC = curses.A_ITALIC

# Define the public API
__all__ = [
    "INVERT", "RED", "GREEN", "ORANGE", "BLUE", "GUTTER", "CYAN", "WHITE",
    "DARK_GREY", "LIGHT_RED", "LIGHT_GREEN", "YELLOW", "LIGHT_BLUE", "PURPLE",
    "BRIGHT_YELLOW", "DIM_WHITE", "NORMAL", "BOLD", "ITALIC", "init_16_colors"
]

def hex_to_rgb(hexstring):
    r = int(int(hexstring[0:2], 16) * 1000 / 255)
    g = int(int(hexstring[2:4], 16) * 1000 / 255)
    b = int(int(hexstring[4:6], 16) * 1000 / 255)
    return (r, g, b)

# Define RGB colors
green = hex_to_rgb("29ad2b")
brown = hex_to_rgb("896018")
white = hex_to_rgb("ffffff")
bright_yellow = hex_to_rgb("ffd75e")
bright_blue = hex_to_rgb("3169f1")

tn_bg = hex_to_rgb("24283b")
tn_bg_dark = hex_to_rgb("1f2335")
tn_bg_highlight = hex_to_rgb("292e42")
tn_blue = hex_to_rgb("7aa2f7")
tn_blue0 = hex_to_rgb("3d59a1")
tn_blue1 = hex_to_rgb("2ac3de")
tn_blue2 = hex_to_rgb("0db9d7")
tn_blue5 = hex_to_rgb("89ddff")
tn_blue6 = hex_to_rgb("b4f9f8")
tn_blue7 = hex_to_rgb("394b70")
tn_comment = hex_to_rgb("565f89")
tn_cyan = hex_to_rgb("7dcfff")
tn_dark3 = hex_to_rgb("545c7e")
tn_dark5 = hex_to_rgb("737aa2")
tn_fg = hex_to_rgb("c0caf5")
tn_fg_dark = hex_to_rgb("a9b1d6")
tn_fg_gutter = hex_to_rgb("3b4261")
tn_green = hex_to_rgb("9ece6a")
tn_green1 = hex_to_rgb("73daca")
tn_green2 = hex_to_rgb("41a6b5")
tn_magenta = hex_to_rgb("bb9af7")
tn_magenta2 = hex_to_rgb("ff007c")
tn_orange = hex_to_rgb("ff9e64")
tn_purple = hex_to_rgb("9d7cd8")
tn_red = hex_to_rgb("f7768e")
tn_red1 = hex_to_rgb("db4b4b")
tn_teal = hex_to_rgb("1abc9c")
tn_terminal_black = hex_to_rgb("414868")
tn_yellow = hex_to_rgb("e0af68")
tn_git_add = hex_to_rgb("449dab")
tn_git_change = hex_to_rgb("6183bb")
tn_git_delete = hex_to_rgb("914c54")

# Color indices
COLOR_BLACK = 0
COLOR_RED = 1
COLOR_GREEN = 2
COLOR_ORANGE = 3
COLOR_BLUE = 4
COLOR_GUTTER = 5
COLOR_CYAN = 6
COLOR_WHITE = 7
COLOR_DARK_GREY = 8
COLOR_LIGHT_RED = 9
COLOR_LIGHT_GREEN = 10
COLOR_YELLOW = 11
COLOR_LIGHT_BLUE = 12
COLOR_PURPLE = 13
COLOR_BRIGHT_YELLOW = 14
COLOR_DIM_WHITE = 15

# Color definitions
color_definitions = {
    COLOR_BLACK: tn_terminal_black,
    COLOR_RED: tn_red1,
    COLOR_GREEN: green,
    COLOR_ORANGE: tn_orange,
    COLOR_BLUE: bright_blue,
    COLOR_GUTTER: tn_fg_gutter,
    COLOR_CYAN: tn_cyan,
    COLOR_WHITE: white,
    COLOR_DARK_GREY: tn_dark5,
    COLOR_LIGHT_RED: tn_red,
    COLOR_LIGHT_GREEN: tn_green,
    COLOR_YELLOW: tn_yellow,
    COLOR_LIGHT_BLUE: tn_blue,
    COLOR_PURPLE: tn_purple,
    COLOR_BRIGHT_YELLOW: bright_yellow,
    COLOR_DIM_WHITE: tn_fg,
}

# Initialize 16 colors
def init_16_colors():
    curses.start_color()
    if curses.can_change_color():
        for color, rgb in color_definitions.items():
            curses.init_color(color, *rgb)

    # Define color pairs
    curses.init_pair(1, COLOR_WHITE, COLOR_GUTTER)
    curses.init_pair(2, COLOR_RED, -1)
    curses.init_pair(3, COLOR_GREEN, -1)
    curses.init_pair(4, COLOR_ORANGE, -1)
    curses.init_pair(5, COLOR_BLUE, -1)
    curses.init_pair(6, COLOR_GUTTER, -1)
    curses.init_pair(7, COLOR_CYAN, -1)
    curses.init_pair(8, COLOR_WHITE, -1)
    curses.init_pair(9, COLOR_DARK_GREY, -1)
    curses.init_pair(10, COLOR_LIGHT_RED, -1)
    curses.init_pair(11, COLOR_LIGHT_GREEN, -1)
    curses.init_pair(12, COLOR_YELLOW, -1)
    curses.init_pair(13, COLOR_LIGHT_BLUE, -1)
    curses.init_pair(14, COLOR_PURPLE, -1)
    curses.init_pair(15, COLOR_BRIGHT_YELLOW, -1)
    curses.init_pair(16, COLOR_DIM_WHITE, -1)

    global INVERT, RED, GREEN, ORANGE, BLUE, GUTTER, CYAN, WHITE
    global DARK_GREY, LIGHT_RED, LIGHT_GREEN, YELLOW, LIGHT_BLUE
    global PURPLE, BRIGHT_YELLOW, DIM_WHITE, NORMAL, BOLD, ITALIC

    INVERT = curses.color_pair(1)
    RED = curses.color_pair(2)
    GREEN = curses.color_pair(3)
    ORANGE = curses.color_pair(4)
    BLUE = curses.color_pair(5)
    GUTTER = curses.color_pair(6)
    CYAN = curses.color_pair(7)
    WHITE = curses.color_pair(8)
    DARK_GREY = curses.color_pair(9)
    LIGHT_RED = curses.color_pair(10)
    LIGHT_GREEN = curses.color_pair(11)
    YELLOW = curses.color_pair(12)
    LIGHT_BLUE = curses.color_pair(13)
    PURPLE = curses.color_pair(14)
    BRIGHT_YELLOW = curses.color_pair(15)
    DIM_WHITE = curses.color_pair(16)

    NORMAL = curses.A_NORMAL
    BOLD = curses.A_BOLD
    ITALIC = curses.A_ITALIC
