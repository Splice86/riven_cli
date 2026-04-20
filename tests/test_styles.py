"""Tests for src/styles.py"""

import pytest


class TestStylesConstants:
    """Tests that ANSI constants are defined and non-empty."""

    def test_color_constants_are_strings(self):
        """All color constants should be non-empty strings."""
        from src import styles

        for name in ["RED", "GREEN", "YELLOW", "CYAN", "MAGENTA", "WHITE", "GREY"]:
            val = getattr(styles, name)
            assert isinstance(val, str), f"{name} should be str"
            assert len(val) > 0, f"{name} should not be empty"

    def test_effect_constants(self):
        """BOLD, DIM, RESET should be defined."""
        from src import styles

        assert isinstance(styles.BOLD, str)
        assert isinstance(styles.DIM, str)
        assert isinstance(styles.RESET, str)

    def test_ansi_codes_are_actually_ansi(self):
        """ANSI codes should start with \\033[."""
        from src import styles

        for name in ["RED", "GREEN", "CYAN", "RESET", "BOLD"]:
            val = getattr(styles, name)
            assert val.startswith("\033["), f"{name} should be ANSI escape code"


class TestSections:
    """Tests for section definitions."""

    def test_all_sections_defined(self):
        """thinking, tool, result, riven, error sections should exist."""
        from src.styles import SECTIONS

        for section in ["thinking", "tool", "result", "riven", "error"]:
            assert section in SECTIONS, f"{section} should be in SECTIONS"

    def test_sections_have_required_keys(self):
        """Each section should have heading_bg, heading_color, label."""
        from src.styles import SECTIONS

        required = {"heading_bg", "heading_color", "label"}
        for name, section in SECTIONS.items():
            missing = required - set(section.keys())
            assert not missing, f"section '{name}' missing keys: {missing}"


class TestSectionHeader:
    """Tests for section_header()."""

    def test_returns_string(self):
        """section_header() should return a string."""
        from src.styles import section_header

        result = section_header("thinking")
        assert isinstance(result, str)

    def test_known_section_uses_correct_style(self):
        """Known section should use that section's heading styles."""
        from src.styles import section_header, SECTIONS

        for name in SECTIONS:
            result = section_header(name)
            assert SECTIONS[name]["heading_bg"] in result
            assert SECTIONS[name]["heading_color"] in result
            assert SECTIONS[name]["label"] in result

    def test_unknown_section_falls_back_to_thinking(self):
        """Unknown section name should fall back to 'thinking' style."""
        from src.styles import section_header, SECTIONS

        result = section_header("nonexistent_section")
        thinking = SECTIONS["thinking"]
        assert thinking["heading_bg"] in result
        assert thinking["heading_color"] in result


class TestSectionContent:
    """Tests for section_content()."""

    def test_returns_string_with_text(self):
        """section_content() should return text wrapped in styling."""
        from src.styles import section_content, SECTIONS

        result = section_content("riven", "hello world")
        assert "hello world" in result

    def test_unknown_section_falls_back_to_thinking(self):
        """Unknown section should fall back to thinking style."""
        from src.styles import section_content, SECTIONS

        result = section_content("not_a_section", "text")
        thinking = SECTIONS["thinking"]
        assert thinking["content_color"] in result


class TestTruncateOutput:
    """Tests for truncate_output()."""

    def test_short_text_unchanged(self):
        """Short text under limits should be returned unchanged."""
        from src.styles import truncate_output

        text = "short\noutput"
        result = truncate_output(text)
        assert result == text
        assert "... truncated ..." not in result

    def test_truncates_to_max_lines(self):
        """Text exceeding MAX_LINES should be truncated."""
        from src.styles import truncate_output, MAX_LINES

        lines = ["line"] * (MAX_LINES + 5)
        text = "\n".join(lines)
        result = truncate_output(text)
        result_lines = result.split("\n")
        assert len(result_lines) <= MAX_LINES + 1  # +1 for truncation message
        assert "... truncated ..." in result

    def test_truncates_long_lines(self):
        """Lines exceeding MAX_LINE_LENGTH should be truncated."""
        from src.styles import truncate_output, MAX_LINE_LENGTH

        long_line = "x" * (MAX_LINE_LENGTH + 50)
        result = truncate_output(long_line)
        assert "... truncated ..." in result
        # Check the truncated line
        first_line = result.split("\n")[0]
        assert len(first_line) <= MAX_LINE_LENGTH


class TestMaxLineLength:
    """Tests that magic numbers are defined as constants."""

    def test_max_lines_is_defined(self):
        """MAX_LINES should be a positive integer."""
        from src.styles import MAX_LINES

        assert isinstance(MAX_LINES, int)
        assert MAX_LINES > 0

    def test_max_line_length_is_defined(self):
        """MAX_LINE_LENGTH should be a positive integer."""
        from src.styles import MAX_LINE_LENGTH

        assert isinstance(MAX_LINE_LENGTH, int)
        assert MAX_LINE_LENGTH > 0
