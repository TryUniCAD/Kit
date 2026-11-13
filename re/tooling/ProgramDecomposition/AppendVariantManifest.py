from __future__ import annotations
import argparse as Argparse
import ast as AstLib
from pathlib import Path as PathInfo

from black import FileMode as BlackMode, format_str as FormatSource
from ProgramReader import ReadAssigns


def MainRun() -> int:
    Parser = Argparse.ArgumentParser()
    Parser.add_argument("current", type=PathInfo)
    Parser.add_argument("addition", type=PathInfo)
    Parser.add_argument("variant")
    Arguments = Parser.parse_args()
    CurrentText = Arguments.current.read_text(encoding="utf-8")
    CurrentAssigns = ReadAssigns(AstLib.parse(CurrentText))
    AdditionAssigns = ReadAssigns(AstLib.parse(Arguments.addition.read_text(encoding="utf-8")))
    NewRecords = AdditionAssigns["KProgramManifest"][1]
    if len(NewRecords) != 1 or NewRecords[0][0] != Arguments.variant:
        raise ValueError("addition is not the requested single variant")
    NewRecord = NewRecords[0]
    ExistingRecords = CurrentAssigns["KProgramManifest"][1]
    if any(Record[0] == Arguments.variant for Record in ExistingRecords):
        raise ValueError("variant is already registered")
    ExistingGlobals = CurrentAssigns["KGlobalStats"][1]
    AdditionGlobals = AdditionAssigns["KGlobalStats"][1]
    if len(ExistingGlobals) != 6 or len(AdditionGlobals) != 6:
        raise ValueError("global statistic shape mismatch")
    CombinedGlobals = tuple(Existing + Added for Existing, Added in zip(ExistingGlobals, AdditionGlobals, strict=True))
    CurrentText = CurrentText.replace("KGlobalStats = " + repr(ExistingGlobals), "KGlobalStats = " + repr(CombinedGlobals), 1)
    SourceLines = CurrentText.splitlines()
    InsertAt = next(Index for Index, Line in enumerate(SourceLines) if Line == ")" )
    SourceLines[InsertAt:InsertAt] = ["    " + repr(NewRecord) + ",", ""]
    Arguments.current.write_text(FormatSource("\n".join(SourceLines), mode=BlackMode()), encoding="utf-8", newline="\n")
    print(f"registered {Arguments.variant}: {CombinedGlobals}")
    return 0


if __name__ == "__main__":
    raise SystemExit(MainRun())
