"""
parser.py

Finds all .py files in an uploaded project and parses each into an AST
(Abstract Syntax Tree) — the structured, tree-shaped representation of
code that Python itself understands.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


IGNORED_DIR_NAMES = {
    ".git", ".venv", "venv", "env", "__pycache__",
    "node_modules", "build", "dist", ".idea", ".vscode",
}


@dataclass
class ParsedFile:
    """A single Python source file: its path, raw text, and parsed AST."""
    path: Path
    relative_path: str
    source: str
    tree: Optional[ast.AST]
    parse_error: Optional[str] = None


def _should_ignore(path: Path) -> bool:
    """True if any part of the path is inside an ignored directory."""
    return any(part in IGNORED_DIR_NAMES for part in path.parts)


def discover_python_files(project_root: Path) -> List[Path]:
    """Recursively find every .py file under project_root, skipping junk folders."""
    project_root = Path(project_root)
    py_files = [
        p for p in project_root.rglob("*.py")
        if p.is_file() and not _should_ignore(p.relative_to(project_root))
    ]
    return sorted(py_files)


def parse_file(path: Path, project_root: Path) -> ParsedFile:
    """Read a single .py file and parse it into an AST."""
    path = Path(path)
    relative_path = str(path.relative_to(project_root))

    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return ParsedFile(path, relative_path, "", None, f"Could not read file: {exc}")

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return ParsedFile(path, relative_path, source, None,
                           f"SyntaxError: {exc.msg} (line {exc.lineno})")

    return ParsedFile(path, relative_path, source, tree, None)


def load_project(project_root: Path) -> List[ParsedFile]:
    """Discover and parse every .py file in a project directory."""
    project_root = Path(project_root)
    py_files = discover_python_files(project_root)
    return [parse_file(p, project_root) for p in py_files]
