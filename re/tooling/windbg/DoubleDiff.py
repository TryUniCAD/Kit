from __future__ import annotations
import json as JsonData
import struct as Struct
import sys as System
from pathlib import Path as PathInfo

KRootInfo = PathInfo(__file__).resolve().parents[2]
for Candidate in (KRootInfo, KRootInfo / "src"):
    if str(Candidate) not in System.path:
        System.path.insert(0, str(Candidate))
from convert.adapters.solidworks.container.Container import SldprtArchive
from convert.adapters.solidworks.container.Format import RESOLVED_FEATURES_STREAM as ResolvedStream


def MainRun() -> int:
    if len(System.argv) != 5:
        raise SystemExit("usage: DoubleDiff.py left.SLDPRT right.SLDPRT left_mm right_mm")
    LeftPart = PathInfo(System.argv[1])
    RightPart = PathInfo(System.argv[2])
    LeftMillimetres = float(System.argv[3])
    RightMillimetres = float(System.argv[4])
    LeftBlob = SldprtArchive.open(LeftPart).require(ResolvedStream)
    RightBlob = SldprtArchive.open(RightPart).require(ResolvedStream)
    LeftBytes = Struct.pack("<d", LeftMillimetres / 1000.0)
    Rows = []
    for Offset in range(0, min(len(LeftBlob), len(RightBlob)) - 7):
        if LeftBlob[Offset : Offset + 8] != LeftBytes:
            continue
        Rows.append(
            {
                "offset": Offset,
                "left": Struct.unpack_from("<d", LeftBlob, Offset)[0],
                "right": Struct.unpack_from("<d", RightBlob, Offset)[0],
            }
        )
    print(JsonData.dumps({"left": str(LeftPart), "right": str(RightPart), "left_mm": LeftMillimetres, "right_mm": RightMillimetres, "matches": Rows}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(MainRun())
