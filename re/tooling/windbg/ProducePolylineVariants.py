from __future__ import annotations
import json as JsonData
from pathlib import Path as PathInfo
import sys as System

Root = PathInfo(__file__).resolve().parents[3]
for Candidate in (Root, Root / "src"):
    if str(Candidate) not in System.path:
        System.path.insert(0, str(Candidate))
from convert import write_document as WriteDoc
from tests.convert.solidworks.resolved.SolidworksPolylineFiveTests import BuildDocument


def MainRun() -> int:
    Shifted = ((5.0, -10.0), (45.0, -5.0), (35.0, 25.0), (12.0, 37.0), (-8.0, 12.0))
    Control = ((0.0, 0.0), (35.0, 0.0), (42.0, 17.0), (19.0, 32.0), (-5.0, 14.0))
    Cases = (
        ("control9", BuildDocument(Control, Depth=9.0)),
        ("shifted37", BuildDocument(Shifted, Depth=37.0)),
    )
    for Label, Document in Cases:
        Target = Root / ".rescratch" / "polyline" / f"kit-five-public-{Label}.SLDPRT"
        Result = WriteDoc(Document, Target, allow_carrier=False)
        print(JsonData.dumps({"label": Label, "target": str(Target), "vendor_loadable": Result.IsVendorLoadable, "application_usable": Result.IsAppUsable, "near_lossless": Result.IsNearLossless, "diagnostics": [str(Item) for Item in Result.diagnostics]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(MainRun())
