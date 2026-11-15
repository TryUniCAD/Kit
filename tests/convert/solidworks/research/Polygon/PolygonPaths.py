from __future__ import annotations

# isolation needs the audit boundary before builder imports can inspect data
KPaths = """
import sys as SysValue
from codecs import lookup as FindCodec
from json import dumps as DumpJson
from math import cos as CosValue, sin as SinValue, tau as TauValue
from pathlib import Path as FilePath

RepoRoot = FilePath(SysValue.argv[1])
Scenario = SysValue.argv[2]
Count = int(SysValue.argv[3])
Depth = float(SysValue.argv[4])
SysValue.dont_write_bytecode = True
SysValue.path.insert(0, str(RepoRoot))
SysValue.path.insert(0, str(RepoRoot / 'src'))
SysValue.path.insert(0, str(RepoRoot / 're' / 'tooling' / 'sw2026'))
SysValue.path.insert(0, str(RepoRoot / 're' / 'tooling' / 'sw2026' / 'serial'))

from tests.convert.solidworks.research.ConstructionGuard import BuildAudit

AuditValue = BuildAudit(RepoRoot / 're' / 'tooling' / 'sw2026' / 'serial' / 'defs')
SysValue.addaudithook(AuditValue.InspectEvent)
"""
