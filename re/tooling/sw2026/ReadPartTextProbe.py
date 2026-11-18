from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]).resolve()
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from convert import open_document
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Container.Container import SldprtArchive

SOURCE = Path(sys.argv[2])
BEFORE = sha256(SOURCE.read_bytes()).hexdigest()
DOCUMENT = open_document(SOURCE, include_brep=False, include_tessellation=False)
ARCHIVE = SldprtArchive.open(SOURCE)
RAW = ARCHIVE.require("Contents/CMgr")
GRAPH = ReadCmgrMut(RAW, 19000)
ROUND_TRIP = WriteCmgrMut(GRAPH.RootValue, 19000)
if ROUND_TRIP != RAW or sha256(SOURCE.read_bytes()).hexdigest() != BEFORE:
    raise ValueError("property read process changed its input or typed manager bytes")

print(json.dumps({
    "schema": "kit.sw2026.part-text-reader-probe.v1",
    "passed": True,
    "source_sha256": BEFORE,
    "cmgr_sha256": sha256(RAW).hexdigest(),
    "cmgr_round_trip": True,
    "cmgr_usage": GRAPH.ReportValue,
    "configuration_manager_map_counter": GRAPH.MapValue.CounterValue,
    "document": json.loads(DOCUMENT.to_json(indent=None)),
    "native_processes_started": 0,
    "vendor_runtime_imports": [name for name in sys.modules if name.startswith(("win32com", "pythoncom"))],
}, ensure_ascii=False, sort_keys=True))
