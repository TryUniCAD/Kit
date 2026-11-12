"""Run every Kit feature acceptance suite in one Fusion session.

Runs the cuboid, extrude, hole, pattern and multi-family wrappers in order.
Each wrapper writes its own Authored/NativeAcceptance*.json report.
Run only through RunLocked.mjs.
"""

import runpy
from pathlib import Path

WRAPPERS = ("AcceptCuboid.py", "AcceptExtrudes.py", "AcceptHoles.py", "AcceptPatterns.py", "AcceptMulti.py")

for wrapper in WRAPPERS:
    runpy.run_path(str(Path(__file__).resolve().parent / wrapper), run_name="kit_feature_suite")
