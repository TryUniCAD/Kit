import json as JsonTools
import sys as SysTools
from pathlib import Path

SourcePath = Path(SysTools.argv[1])
if SourcePath.suffix.lower() != ".json":
    raise SystemExit("expected a .json document")
print(JsonTools.loads(SourcePath.read_text())["count"])
