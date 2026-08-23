from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


PERSONAL_PATH_PATTERN = re.compile(
    r"(?<![A-Za-z0-9._-])(?:[A-Za-z]:[\\/]+Users[\\/]+[A-Za-z0-9._-]+|/(?:Users|home)/[A-Za-z0-9._-]+)"
)

TEXT_SUFFIXES = {
    ".bat",
    ".cmd",
    ".conf",
    ".cfg",
    ".css",
    ".env",
    ".example",
    ".html",
    ".ini",
    ".js",
    ".jsx",
    ".md",
    ".ps1",
    ".py",
    ".sh",
    ".sql",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
    ".json",
}

TEXT_FILENAMES = {
    ".dockerignore",
    ".env",
    ".env.example",
    ".gitignore",
    "Dockerfile",
    "Makefile",
}

SKIP_DIRS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    ".venv",
    "node_modules",
    "dist",
    "build",
}


@dataclass(frozen=True)
class PersonalPathFinding:
    path: str
    line: int
    match: str


def redact_personal_paths(text: str) -> str:
    """Replace personal absolute path prefixes with public-safe placeholders."""
    return PERSONAL_PATH_PATTERN.sub("<USER_HOME>", text)


def scan_personal_paths(repo: Path) -> list[PersonalPathFinding]:
    findings: list[PersonalPathFinding] = []
    for path in iter_text_files(repo):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = path.relative_to(repo).as_posix()
        for index, line in enumerate(text.splitlines(), start=1):
            for match in PERSONAL_PATH_PATTERN.finditer(line):
                findings.append(PersonalPathFinding(path=rel, line=index, match=match.group(0)))
    return findings


def iter_text_files(repo: Path):
    for path in repo.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in TEXT_FILENAMES:
            continue
        yield path
