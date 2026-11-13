from __future__ import annotations
import argparse as Argparse
import ast as AstLib
from pathlib import Path as PathInfo

from ProgramBuilder import SortOwnerKey
from ProgramReader import ReadAssigns
from ProgramRenderer import RenderOwner


def MergeOwners(CurrentRoot: PathInfo, AdditionRoot: PathInfo) -> None:
    for AdditionPath in sorted(AdditionRoot.rglob("*.py")):
        RelativePath = AdditionPath.relative_to(AdditionRoot)
        TargetPath = CurrentRoot / RelativePath
        Addition = dict(ReadAssigns(AstLib.parse(AdditionPath.read_text(encoding="utf-8")))["KOwnerSites"][1])
        Current = dict(ReadAssigns(AstLib.parse(TargetPath.read_text(encoding="utf-8")))["KOwnerSites"][1]) if TargetPath.exists() else {}
        for Key, Value in Current.items():
            if Key in Addition and Addition[Key] != Value:
                raise ValueError(f"conflicting owner site {RelativePath} {Key!r}: {Value!r} versus {Addition[Key]!r}")
            Addition.setdefault(Key, Value)
        Rendered = RenderOwner(tuple(sorted(Addition.items(), key=SortOwnerKey)))
        if not TargetPath.exists() or TargetPath.read_text(encoding="utf-8") != Rendered:
            TargetPath.parent.mkdir(parents=True, exist_ok=True)
            TargetPath.write_text(Rendered, encoding="utf-8", newline="\n")
            print(f"merged {RelativePath}: {len(Current)} retained + {len(Addition) - len(Current)} new")


def MainRun() -> int:
    Parser = Argparse.ArgumentParser()
    Parser.add_argument("current", type=PathInfo)
    Parser.add_argument("addition", type=PathInfo)
    Arguments = Parser.parse_args()
    MergeOwners(Arguments.current, Arguments.addition)
    return 0


if __name__ == "__main__":
    raise SystemExit(MainRun())
