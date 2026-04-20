"""Heading/section styles for Riven CLI output.

Dark goth cyberpunk - neon accents on void black.
"""

# =============================================================================
# Text Colors
# =============================================================================

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
# Section Definitions - heading_bg, content_bg, heading_color, content_color
# =============================================================================

SECTIONS = {
    "thinking": {
        "heading_bg": GREY,
        "heading_color": WHITE,
        "content_bg": "",
        "content_color": CYAN,
        "label": "[MIND]",
    },
    "tool": {
        "heading_bg": MAGENTA,
        "heading_color": WHITE,
        "content_bg": "",
        "content_color": WHITE,
        "label": "[EXEC]",
    },
    "result": {
        "heading_bg": CYAN,
        "heading_color": WHITE,
        "content_bg": "",
        "content_color": GREEN,
        "label": "[DATA]",
    },
    "riven": {
        "heading_bg": "",
        "heading_color": CYAN,
        "content_bg": "",
        "content_color": WHITE,
        "label": "[RIVEN]",
    },
    "error": {
        "heading_bg": GREY,
        "heading_color": RED,
        "content_bg": "",
        "content_color": RED,
        "label": "[ERR]",
    },
}


def section_header(name: str) -> str:
    """Generate styled section header with heading_bg and heading_color."""
    if name not in SECTIONS:
        name = "thinking"
    section = SECTIONS[name]
    return f"\n{section['heading_bg']}{BOLD}{section['heading_color']} {section['label']} {RESET}"


def section_content(name: str, text: str) -> str:
    """Generate styled content with content_bg and content_color."""
    if name not in SECTIONS:
        name = "thinking"
    section = SECTIONS[name]
    return f"{section['content_bg']}{section['content_color']}{text}{RESET}"


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
