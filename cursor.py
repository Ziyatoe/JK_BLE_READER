import sys
import time

# Text Styles
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
UNDERLINE = "\033[4m"
BLINK = "\033[5m"
REVERSE = "\033[7m"

# Standard Colors
BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

# Bright Colors (Light Versions)
LBLACK = "\033[1;30m"   # Gray
LRED = "\033[1;31m"     # Light Red
LGREEN = "\033[1;32m"   # Light Green
LYELLOW = "\033[1;33m"  # Light Yellow
LBLUE = "\033[1;34m"    # Light Blue
LMAGENTA = "\033[1;35m" # Light Magenta
LCYAN = "\033[1;36m"    # Light Cyan
LWHITE = "\033[1;37m"   # Bright White

# Background Colors
BG_BLACK = "\033[40m"
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE = "\033[44m"
BG_MAGENTA = "\033[45m"
BG_CYAN = "\033[46m"
BG_WHITE = "\033[47m"

# Bright Background Colors
BG_LBLACK = "\033[100m"   # Gray Background
BG_LRED = "\033[101m"     # Light Red Background
BG_LGREEN = "\033[102m"   # Light Green Background
BG_LYELLOW = "\033[103m"  # Light Yellow Background
BG_LBLUE = "\033[104m"    # Light Blue Background
BG_LMAGENTA = "\033[105m" # Light Magenta Background
BG_LCYAN = "\033[106m"    # Light Cyan Background
BG_LWHITE = "\033[107m"   # Bright White Background

# Example Usage
# print(f"{BOLD}{RED}This is bold red text{RESET}")
# print(f"{LBLUE}This is light blue text{RESET}")
# print(f"{BG_YELLOW}{BLACK}Black text on yellow background{RESET}")
# print(f"{BG_LRED}{WHITE}White text on light red background{RESET}")

def rotating_cursor(duration=5):
    #---------------------------------------------------------------------------------------------
    cursor_chars = "\/|-"
    for _ in range(int(duration / 0.5)):
        for char in cursor_chars:
            sys.stdout.write(f"\r{char}")  # Overwrite the same line
            sys.stdout.flush()
            time.sleep(0.5)
    sys.stdout.write("\r ")  # Clear the cursor at the end
    sys.stdout.flush()
#---------------------------------------------------------------------------------------------
