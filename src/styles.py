"""Styling definitions for Riven CLI output.

Centralized color/style definitions for consistent terminal output.
"""

# =============================================================================
# Text Colors (bright, readable on dark backgrounds)
# =============================================================================

TEXT_WHITE = "\033[97m"      # Bright white - primary text on colored backgrounds
TEXT_RED = "\033[91m"        # Bright red - errors
TEXT_GREEN = "\033[92m"      # Bright green - success
TEXT_YELLOW = "\033[93m"     # Bright yellow - warnings
TEXT_BLUE = "\033[94m"       # Bright blue - links/urls
TEXT_CYAN = "\033[96m"       # Bright cyan - info
TEXT_MAGENTA = "\033[95m"    # Bright magenta - highlights

# Dim/faded colors for subtle elements
DIM_GREY = "\033[90m"
DIM = "\033[2m"
TEXT_DIM = "\033[2m"

TEXT_BLACK = "\033[30m"      # Black text - good on light backgrounds

RESET = "\033[0m"

# =============================================================================
# Background Colors
# =============================================================================

BG_GREY = "\033[100m"        # Dark grey background
BG_RED = "\033[41m"          # Red background
BG_GREEN = "\033[42m"        # Green background
BG_YELLOW = "\033[43m"       # Yellow background
BG_BLUE = "\033[44m"         # Blue background
BG_MAGENTA = "\033[45m"      # Magenta background
BG_CYAN = "\033[46m"         # Cyan background
BG_WHITE = "\033[47m"        # White background

# =============================================================================
# Section Definitions
# =============================================================================

SECTIONS = {
    "thinking": {
        "label": "THINKING",
        "bg": BG_GREY,
        "title_color": TEXT_WHITE,
        "content_color": TEXT_WHITE,
    },
    "tool": {
        "label": "TOOL",
        "bg": BG_MAGENTA,
        "title_color": TEXT_WHITE,
        "content_color": TEXT_WHITE,
    },
    "result": {
        "label": "RESULT",
        "bg": BG_YELLOW,
        "title_color": TEXT_BLUE,      # Blue title on yellow
        "content_color": TEXT_BLACK,   # Black text on yellow (readable)
    },
    "riven": {
        "label": "RIVEN",
        "bg": BG_CYAN,
        "title_color": TEXT_WHITE,
        "content_color": TEXT_CYAN,    # Cyan content text
    },
    "error": {
        "label": "ERROR",
        "bg": BG_RED,
        "title_color": TEXT_WHITE,
        "content_color": TEXT_WHITE,
    },
}


def section_header(name: str) -> str:
    """Generate a styled section header using title_color."""
    if name not in SECTIONS:
        name = "thinking"
    section = SECTIONS[name]
    return f"\n{section['bg']}{section['title_color']} ▸ {section['label']} {RESET}"


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

MAX_LINES = 4           # Max lines to show before truncation
MAX_LINE_LENGTH = 150   # Max characters per line before truncation
TRUNCATE_MARKER = f"{TEXT_DIM}{DIM}... [{MAX_LINES} lines truncated, use /expand to see full] ...{RESET}"


def truncate_output(text: str) -> str:
    """Truncate output to MAX_LINES lines and MAX_LINE_LENGTH chars per line.
    
    Args:
        text: Raw output text
    
    Returns:
        Truncated text with marker if truncated, original text otherwise
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
        return '\n'.join(truncated_lines) + f"\n{TRUNCATE_MARKER}"
    
    return text
