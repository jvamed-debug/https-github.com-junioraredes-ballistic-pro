"""Source-level guards for the Streamlit rendering modules.

These modules build HTML as strings and hand it to st.markdown. Nothing
imports them in a unit test, so a mistake in the string plumbing only
surfaces when a user opens the tab. The performance dashboard shipped broken
for exactly that reason: a str.format() call over a template that carried an
f-string expression, so .format went looking for a key named
'html_escape(user_info' and raised KeyError on every render.

Checking the source is crude, but it catches the whole class cheaply.
"""

import ast
import pathlib

import pytest

RENDER_DIRS = ["modules", "components", "ui"]


def _python_files():
    root = pathlib.Path(__file__).resolve().parent.parent
    for directory in RENDER_DIRS:
        for path in sorted((root / directory).glob("*.py")):
            if path.name != "__init__.py":
                yield path


ALL_FILES = list(_python_files())


def test_there_are_render_modules_to_check():
    """Otherwise every test below passes by iterating nothing."""
    assert len(ALL_FILES) >= 5


@pytest.mark.parametrize("path", ALL_FILES, ids=lambda p: p.name)
def test_no_format_call_over_an_fstring_expression(path):
    """A literal '{name(' or '{obj[' inside a .format() template means an
    f-string expression was left in a string that is not an f-string."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    offenders = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "format"):
            continue
        target = func.value
        if not (isinstance(target, ast.Constant) and isinstance(target.value, str)):
            continue

        template = target.value
        for i, char in enumerate(template):
            if char != "{":
                continue
            closing = template.find("}", i)
            if closing == -1:
                continue
            field = template[i + 1:closing]
            if "(" in field or "[" in field:
                offenders.append((node.lineno, field[:60]))

    assert not offenders, (
        f"{path.name}: .format() template carries an f-string expression "
        f"{offenders}. Make the string an f-string, or pass a plain name."
    )


@pytest.mark.parametrize("path", ALL_FILES, ids=lambda p: p.name)
def test_modules_parse(path):
    """A syntax error here never reaches the test suite otherwise."""
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
