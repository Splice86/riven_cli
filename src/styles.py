"""Styling definitions for Riven CLI output.

Dark goth cyberpunk - neon accents on void black.
"""

# =============================================================================
# Text Colors
# =============================================================================

BLACK = ""
WHITE = "\033[97m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"

# Dim/faded
GREY = "\033[90m"
DIM = "\033[2m"

RESET = "\033[0m"
BOLD = "\033[1m"

# =============================================================================
# Section Colors - configure heading/content/bg per section
# =============================================================================

SECTIONS = {
    "thinking": {
        "heading_color": WHITE,
        "content_color": CYAN,
        "bg": GREY,
        "label": "[MIND]",
    },
    "tool": {
        "heading_color": WHITE,
        "content_color": WHITE,
        "bg": MAGENTA,
        "label": "[EXEC]",
    },
    "result": {
        "heading_color": WHITE,
        "content_color": GREEN,
        "bg": CYAN,
        "label": "[DATA]",
    },
    "riven": {
        "heading_color": CYAN,
        "content_color": WHITE,
        "bg": BLACK,         # No bg - just neon text
        "label": "[RIVEN]",
    },
    "error": {
        "heading_color": WHITE,
        "content_color": RED,
        "bg": GREY,
        "label": "[ERR]",
    },
}


def section_header(name: str) -> str:
    """Generate a styled section header.

    Bold white heading on colored bg.
    """
    if name not in SECTIONS:
        name = "thinking"
    section = SECTIONS[name]
    return f"\n{section['bg']}{BOLD}{section['heading_color']} {section['label']} {RESET}"


def section_content(name: str, text: str) -> str:
    """Color text using section's content_color."""
    if name not in SECTIONS:
        name = "thinking"
    section = SECTIONS[name]
    return f"{section['content_color']}{text}{RESET}"


# =============================================================================
# Truncation Config
# =============================================================================

MAX_LINES = 10
MAX_LINE_LENGTH = 200


def truncate_output(text: str) -> str:
    """Truncate output to MAX_LINES lines and MAX_LINE_LENGTH chars."""
    lines = text.split('\n')

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
