"""Make `src/` importable for pytest without depending on the editable install's
.pth-based sys.path injection, which has been observed to intermittently not get
processed in this project's dev environment (see docs/research.md decisions log /
project memory) even though `pip install -e .` reports success. Cheap and harmless
when the editable install *is* working -- the path just ends up listed twice.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
