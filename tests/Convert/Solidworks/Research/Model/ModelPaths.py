from __future__ import annotations

# isolated interpreter setup prevents ambient imports from hiding missing construction dependencies
KImports = """
from json import dumps as EncodeJson
import sys as SystemLib
from pathlib import Path as FilePath

WorkRoot = FilePath(SystemLib.argv[1])
CountCfg = int(SystemLib.argv[2])
DensityVal = float(SystemLib.argv[3])
NamePrefix = SystemLib.argv[4]
SystemLib.dont_write_bytecode = True
SystemLib.path.insert(0, str(WorkRoot))
SystemLib.path.insert(0, str(WorkRoot / "src"))
SystemLib.path.insert(0, str(WorkRoot / "re" / "tooling" / "sw2026"))
SystemLib.path.insert(0, str(WorkRoot / "re" / "tooling" / "sw2026" / "serial"))
"""
