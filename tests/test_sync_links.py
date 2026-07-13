"""Tests de idempotencia de sync_links."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_sync_links_idempotente():
  result1 = subprocess.run(
      [sys.executable, str(ROOT / "scripts" / "sync_links.py"), "--check"],
      cwd=ROOT,
      capture_output=True,
      text=True,
  )
  subprocess.run(
      [sys.executable, str(ROOT / "scripts" / "sync_links.py")],
      cwd=ROOT,
      check=True,
  )
  result2 = subprocess.run(
      [sys.executable, str(ROOT / "scripts" / "sync_links.py"), "--check"],
      cwd=ROOT,
      capture_output=True,
      text=True,
  )
  assert result2.returncode == 0, result2.stdout + result2.stderr
