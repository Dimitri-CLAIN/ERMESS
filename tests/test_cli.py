import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_cli_runs_headless(tmp_path):
    output = tmp_path / "out.xlsx"
    result = subprocess.run(
        [sys.executable, str(REPO / "ERMESS_Pro.py"),
         "--input", str(REPO / "inputs_ERMESS_pro_example.xlsx"),
         "--output", str(output),
         "--generations", "2"],
        cwd=tmp_path,
        env={**os.environ, "ERMESS_POOL_SIZE": "2"},
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr[-2000:]
    assert output.is_file()
    progress = [line for line in result.stdout.splitlines() if line.startswith("ERMESS_PROGRESS ")]
    assert [line.split()[1] for line in progress] == ["generation=1", "generation=2"]
