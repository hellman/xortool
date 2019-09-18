from xortool.libcolors import color

C_RESET = color()
C_FATAL = color("red")
C_WARN = color("yellow")

C_KEYLEN = color("green")
C_PROB = color("white", attrs="")
C_BEST_KEYLEN = color("green", attrs="bold")
C_BEST_PROB = color("white", attrs="bold")

C_DIV = color(attrs="bold")

C_KEY = color("red", attrs="bold")
C_BOLD = color(attrs="bold")
C_COUNT = color("yellow", attrs="bold")

COLORS = {
    'C_RESET': C_RESET,
    'C_FATAL': C_FATAL,
    'C_WARN': C_WARN,
    'C_KEYLEN': C_KEYLEN,
    'C_PROB': C_PROB,
    'C_BEST_KEYLEN': C_BEST_KEYLEN,
    'C_BEST_PROB': C_BEST_PROB,
    'C_DIV': C_DIV,
    'C_KEY': C_KEY,
    'C_BOLD': C_BOLD,
    'C_COUNT': C_COUNT,
}
