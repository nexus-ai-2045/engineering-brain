from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_json_output_is_utf8_even_when_parent_requests_cp932() -> None:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "cp932"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "engineering_brain",
            "gate",
            "--trigger",
            "implementation",
            "--json",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    output = completed.stdout.decode("utf-8")
    assert "ユーザー可視の判断" in output


def test_help_output_is_utf8_even_when_parent_requests_cp932() -> None:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "cp932"
    completed = subprocess.run(
        [sys.executable, "-m", "engineering_brain", "--help"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    output = completed.stdout.decode("utf-8")
    assert "定番アルゴリズム" in output
