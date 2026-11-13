from __future__ import annotations
import argparse as Argparse
from pathlib import Path as PathInfo


def MainRun() -> int:
    Parser = Argparse.ArgumentParser()
    Parser.add_argument("facade", type=PathInfo)
    Parser.add_argument("typed", type=PathInfo)
    Parser.add_argument("output", type=PathInfo)
    Arguments = Parser.parse_args()
    Facade = Arguments.facade.read_text(encoding="utf-8")
    Typed = Arguments.typed.read_text(encoding="utf-8")
    OwnerStart = Typed.index("FieldOwners = (")
    OperationsStart = Typed.index("ResolvedOps = (")
    FormatsStart = Typed.index("PrimitiveFormats =")
    OwnerTable = Typed[OwnerStart:OperationsStart].replace("FieldOwners = (", "KFieldOwners = (", 1)
    OperationTable = Typed[OperationsStart:FormatsStart].replace("ResolvedOps = (", "KResolvedOps = (", 1)
    Marker = "KPointOffsets = ("
    if Marker not in Facade:
        raise ValueError("variant point anchor is missing")
    Source = Facade.replace(Marker, OwnerTable + "\n" + OperationTable + "\n" + Marker, 1)
    Arguments.output.parent.mkdir(parents=True, exist_ok=True)
    Arguments.output.write_text(Source, encoding="utf-8", newline="\n")
    print(f"wrote {Arguments.output} with typed operation tables")
    return 0


if __name__ == "__main__":
    raise SystemExit(MainRun())
