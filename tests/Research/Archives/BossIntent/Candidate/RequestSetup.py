# isolated execution must resolve the exact checkout rather than installed or ambient modules
KRequestSetup = """
import sys
from os import O_CREAT, O_RDWR, O_WRONLY, fsdecode
from pathlib import Path


# the child process needs an explicit checkout anchor under isolated execution
KRoot = Path(sys.argv[1]).resolve()

# isolated children require explicit checkout precedence to exercise the selected writer
sys.path[:0] = [
    str(KRoot / "src"),
    str(KRoot),
    str(KRoot / "re/automation"),
    str(KRoot / "re/solidworks/WriterResearch"),
]
"""
