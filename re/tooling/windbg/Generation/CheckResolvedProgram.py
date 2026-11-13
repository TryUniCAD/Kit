from __future__ import annotations
import argparse as Argparse
import json as JsonData
import sys as System
from pathlib import Path as PathInfo

KRootInfo = PathInfo(__file__).resolve().parents[4]
for Candidate in (KRootInfo, KRootInfo / "src", KRootInfo / "re" / "tooling" / "ProgramDecomposition"):
    if str(Candidate) not in System.path:
        System.path.insert(0, str(Candidate))
from ProgramReader import ReadProgram
from convert.adapters.solidworks.container.Container import SldprtArchive
from convert.adapters.solidworks.container.Format import RESOLVED_FEATURES_STREAM as ResolvedStream
from convert.adapters.solidworks.programs.Common.FieldEncoder import ReplayResolved


def ParseArguments() -> Argparse.Namespace:
    Parser = Argparse.ArgumentParser()
    Parser.add_argument("source", type=PathInfo)
    Parser.add_argument("part", type=PathInfo)
    return Parser.parse_args()


def MainRun() -> int:
    Arguments = ParseArguments()
    Source = Arguments.source.resolve()
    Program = ReadProgram(Source, Source.parent)
    if len(Program.Streams) != 1:
        raise ValueError("expected one resolved stream")
    Operations = Program.Streams[0][1]
    ProgramBytes = ReplayResolved(Operations, Program.ByteStats[0][1])
    ExpectedBytes = SldprtArchive.open(Arguments.part).require(ResolvedStream)
    print(
        JsonData.dumps(
            {
                "variant": Program.VariantPath,
                "operation_count": len(Operations),
                "byte_length": len(ProgramBytes),
                "identical": ProgramBytes == ExpectedBytes,
                "sha256": Program.ByteStats[0][2],
            },
            indent=2,
        )
    )
    return 0 if ProgramBytes == ExpectedBytes else 1


if __name__ == "__main__":
    raise SystemExit(MainRun())
