# d:/game/puzzle/src/const.py
# Constants for the game
# Defines screen size, colors, and timers
# RELEVANT FILES: main.py, src/app.py

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors (R, G, B)
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_RED = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_YELLOW = (255, 255, 0)
COLOR_GRAY = (128, 128, 128)

# Modes / States
STATE_ATTRACT = "ATTRACT"
STATE_TITLE = "TITLE"
STATE_PLAY = "PLAY"
STATE_CONFIRM = "CONFIRM"
STATE_DEV = "DEV"

# Timers (in milliseconds)
TITLE_WAIT_TIME = 3000  # Time to stay on title screen (3 seconds)
PLAY_TIMEOUT = 60000  # 1 minute inactivity to confirm
CONFIRM_TIMEOUT = 10000  # 10 seconds to decide in confirm
MOUSE_MOVE_THRESHOLD = 100  # Pixel squared distance or aggregate movement threshold

STRING_TITLE = "Puzzle Game"
