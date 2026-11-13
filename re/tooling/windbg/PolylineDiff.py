from __future__ import annotations
import json as JsonData
import struct as Struct
import sys as System
from pathlib import Path as PathInfo

KRootInfo = PathInfo(__file__).resolve().parents[3]
for Candidate in (KRootInfo, KRootInfo / "src"):
    if str(Candidate) not in System.path:
        System.path.insert(0, str(Candidate))
from convert.adapters.solidworks.container.Container import SldprtArchive
from convert.adapters.solidworks.container.Format import RESOLVED_FEATURES_STREAM as ResolvedStream


def Coordinates(text: str) -> tuple[float, ...]:
    return tuple(float(value) / 1000.0 for value in text.split(","))


def MainRun() -> int:
    if len(System.argv) != 7:
        raise SystemExit("usage: PolylineDiff.py first second first_x first_y second_x second_y")
    FirstBlob = SldprtArchive.open(System.argv[1]).require(ResolvedStream)
    SecondBlob = SldprtArchive.open(System.argv[2]).require(ResolvedStream)
    FirstX = Coordinates(System.argv[3])
    FirstY = Coordinates(System.argv[4])
    SecondX = Coordinates(System.argv[5])
    SecondY = Coordinates(System.argv[6])
    Expected = set(zip(FirstX, SecondX, strict=True)) | set(zip(FirstY, SecondY, strict=True))
    if len(FirstX) != len(FirstY) or len(SecondX) != len(SecondY) or len(FirstX) != len(SecondX):
        raise ValueError("point coordinate counts differ")
    Matches = []
    for Offset in range(min(len(FirstBlob), len(SecondBlob)) - 7):
        FirstValue = Struct.unpack_from("<d", FirstBlob, Offset)[0]
        SecondValue = Struct.unpack_from("<d", SecondBlob, Offset)[0]
        for FirstExpected, SecondExpected in Expected:
            if abs(FirstValue - FirstExpected) < 1e-12 and abs(SecondValue - SecondExpected) < 1e-12:
                Matches.append({"offset": Offset, "first": FirstValue, "second": SecondValue})
                break
    print(JsonData.dumps({"matches": Matches}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(MainRun())
