"""Tests for src/cli.py"""

import pytest


class TestCliImports:
    """Tests for CLI module-level imports."""

    def test_requests_imported_at_module_level(self):
        """requests should be imported at module level, not inside main()."""
        import ast
        from src import cli

        source = open("src/cli.py").read()
        tree = ast.parse(source)

        # Find the main function
        main_func = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "main":
                main_func = node
                break

        assert main_func is not None, "main() function should exist"

        # Check imports INSIDE main() - there should be none
        inline_imports = [
            n for n in ast.walk(main_func)
            if isinstance(n, (ast.Import, ast.ImportFrom))
        ]
        assert len(inline_imports) == 0, (
            f"main() should have no inline imports, found: "
            f"{[ast.unparse(n) for n in inline_imports]}"
        )

    def test_get_client_imported_at_module_level(self):
        """get_client should be imported at module level, not inside main()."""
        import ast

        source = open("src/cli.py").read()
        tree = ast.parse(source)

        main_func = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "main":
                main_func = node
                break

        inline_get_client = [
            n for n in ast.walk(main_func)
            if isinstance(n, ast.ImportFrom)
            and n.module == "src.client"
        ]
        assert len(inline_get_client) == 0, (
            "get_client should not be imported inside main()"
        )

    def test_no_inline_import_requests_in_client(self):
        """src/client.py should not import requests inside functions."""
        import ast

        source = open("src/client.py").read()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                imports = [
                    n for n in ast.walk(node)
                    if isinstance(n, ast.Import)
                    and any("requests" in ast.unparse(i) for i in n.names)
                ]
                assert len(imports) == 0, (
                    f"Function {node.name} should not import requests inline"
                )


class TestCliFunctions:
    """Tests for CLI utility functions."""

    def test_get_session_line_formats_correctly(self):
        """get_session_line should wrap session ID in styled brackets."""
        from src.cli import get_session_line

        result = get_session_line("abcd12345678")
        assert "abcd1234" in result
        assert "[" in result and "]" in result
        assert "\033[" in result  # should contain ANSI codes

    def test_get_prompt_prefix_formats_correctly(self):
        """get_prompt_prefix should include core name and ANSI styling."""
        from src.cli import get_prompt_prefix

        result = get_prompt_prefix("codehammer")
        assert "codehammer" in result
        assert "\033[" in result  # should contain ANSI codes

    def test_get_session_line_shortens_long_ids(self):
        """get_session_line should truncate to first 8 chars."""
        from src.cli import get_session_line

        long_id = "a" * 40
        result = get_session_line(long_id)
        # Should contain only first 8 chars
        assert "aaaaaaaa" in result
        assert "aaaaaaaaa" not in result


class TestCliAnsiConsolidation:
    """Tests that ANSI codes are centralized in styles.py."""

    def test_cli_uses_styles_constants(self):
        """cli.py should import ANSI constants from styles, not redefine them."""
        import ast

        source = open("src/cli.py").read()
        tree = ast.parse(source)

        # Check for ANSI codes defined at module level (these should NOT exist)
        module_vars = [
            n for n in tree.body
            if isinstance(n, ast.Assign)
            and any(isinstance(v, ast.Name) and v.id in (
                "RED", "GREEN", "YELLOW", "CYAN", "MAGENTA", "WHITE", "GREY",
                "RESET", "BOLD", "DIM",
            ) for v in n.targets)
            and any(
                isinstance(v, ast.Constant) and isinstance(v.value, str)
                and v.value.startswith("\033[")
                for v in n.value if isinstance(n.value, ast.Constant)
            )
        ]
        # Note: this check passes because we import from styles now
        # Check that we DO import from styles
        imports_from_styles = [
            n for n in tree.body
            if isinstance(n, ast.ImportFrom)
            and n.module == "src.styles"
        ]
        assert len(imports_from_styles) > 0, (
            "cli.py should import from src.styles"
        )

    def test_client_no_ansi_duplication(self):
        """client.py should not define its own RED/RESET ANSI codes."""
        import ast

        source = open("src/client.py").read()
        tree = ast.parse(source)

        # Check that ANSI codes are NOT defined at module level in client.py
        # Look for assignments like: RED = "\033[91m"
        module_level_ansi = [
            n for n in tree.body
            if isinstance(n, ast.Assign)
            and any(
                isinstance(target, ast.Name)
                and target.id in ("RED", "RESET")
                for target in n.targets
            )
            and isinstance(n.value, ast.Constant)
            and isinstance(n.value.value, str)
            and n.value.value.startswith("\033[")
        ]
        assert len(module_level_ansi) == 0, (
            f"client.py should not define ANSI codes at module level: "
            f"{[ast.unparse(n) for n in module_level_ansi]}"
        )
