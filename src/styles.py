"""Styling definitions for Riven CLI output.

Dark goth cyberpunk theme - neon accents on void black.
"""

# =============================================================================
# Text Colors (dark goth cyberpunk)
# =============================================================================

TEXT_CYAN = "\033[96m"       # Electric cyan - primary neon accent
TEXT_MAGENTA = "\033[95m"    # Hot magenta - secondary accent
TEXT_GREEN = "\033[92m"      # Matrix green - success/hacker

# Dim/faded elements
DIM_GREY = "\033[90m"
DIM = "\033[2m"
TEXT_DIM = "\033[2m"

# Basic reset color (inherit from terminal)
RESET = "\033[0m"

# Aliases for compatibility
TEXT_WHITE = TEXT_CYAN      # White-ish cyan for readability
TEXT_RED = TEXT_MAGENTA     # Goth red
TEXT_GREEN = TEXT_GREEN
TEXT_YELLOW = TEXT_GREEN    # Muted green-yellow
TEXT_BLUE = TEXT_CYAN       # Cyan blues
TEXT_ORANGE = TEXT_GREEN    # Muted
TEXT_BLACK = ""

# =============================================================================
# Background Colors (dark as hell)
# =============================================================================

BG_BLACK = "\033[40m"        # True black
BG_DARK_GREY = "\033[100m"   # Dark grey - thinking
BG_DARK_CYAN = "\033[46m"    # Dark cyan - results
BG_DARK_MAGENTA = "\033[45m" # Dark magenta - tools
BG_DARK_GREEN = "\033[42m"   # Dark green - riven output

# Aliases
BG_GREY = BG_DARK_GREY
BG_RED = BG_BLACK
BG_YELLOW = BG_DARK_GREY
BG_BLUE = BG_BLACK
BG_MAGENTA = BG_DARK_MAGENTA
BG_CYAN = BG_DARK_CYAN
BG_WHITE = BG_BLACK
BG_GREEN = BG_DARK_GREEN

# =============================================================================
# Section Definitions - goth cyberpunk labels
# =============================================================================

SECTIONS = {
    "thinking": {
        "label": "[MIND]",
        "bg": BG_DARK_GREY,
        "title_color": TEXT_CYAN,
        "content_color": TEXT_CYAN,
    },
    "tool": {
        "label": "[EXEC]",
        "bg": BG_DARK_MAGENTA,
        "title_color": TEXT_CYAN,
        "content_color": TEXT_CYAN,
    },
    "result": {
        "label": "[DATA]",
        "bg": BG_DARK_CYAN,
        "title_color": TEXT_MAGENTA,
        "content_color": TEXT_GREEN,
    },
    "riven": {
        "label": "[RIVEN]",
        "bg": BG_DARK_GREEN,
        "title_color": TEXT_CYAN,
        "content_color": TEXT_CYAN,
    },
    "error": {
        "label": "[ERR]",
        "bg": BG_BLACK,
        "title_color": TEXT_MAGENTA,
        "content_color": TEXT_MAGENTA,
    },
}


def section_header(name: str) -> str:
    """Generate a styled section header.
    
    Returns newline + colored header with background PERSISTING for content.
    """
    if name not in SECTIONS:
        name = "thinking"
    section = SECTIONS[name]
    return f"\n{section['bg']}{section['title_color']} >> {section['label']}{RESET} "


def section_content(name: str, text: str) -> str:
    """Color text using section's content_color."""
    if name not in SECTIONS:
        name = "thinking"
    section = SECTIONS[name]
    return f"{section['content_color']}{text}{RESET}"


def colored_text(text: str, color: str) -> str:
    """Wrap text in a color."""
    return f"{color}{text}{RESET}"


def error_text(text: str) -> str:
    """Format error text."""
    return f"{TEXT_RED}{text}{RESET}"


def success_text(text: str) -> str:
    """Format success text."""
    return f"{TEXT_GREEN}{text}{RESET}"


# =============================================================================
# Truncation Config
# =============================================================================

MAX_LINES = 10          # Max lines to show before truncation
MAX_LINE_LENGTH = 200   # Max characters per line before truncation


def truncate_output(text: str) -> str:
    """Truncate output to MAX_LINES lines and MAX_LINE_LENGTH chars per line.
    
    Args:
        text: Raw output text
    
    Returns:
        Truncated text if needed, original text otherwise
    """
    lines = text.split('\n')
    
    # Check if truncation needed
    needs_truncation = len(lines) > MAX_LINES
    
    truncated_lines = []
    for line in lines[:MAX_LINES]:
        if len(line) > MAX_LINE_LENGTH:
            truncated_lines.append(line[:MAX_LINE_LENGTH])
            needs_truncation = True
        else:
            truncated_lines.append(line)
    
    if needs_truncation:
        return '\n'.join(truncated_lines) + "\n... truncated ..."
    
    return text
