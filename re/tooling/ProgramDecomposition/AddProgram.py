from __future__ import annotations

import argparse as Argparse
import ast as AstLib
import json as JsonData
from pathlib import Path as PathInfo

from ProgramBuilder import BuildMethods
from ProgramReader import LoadPrograms, ReadAssigns
from ProgramRenderer import (
    BuildStat,
    HashText,
    RenderMethod,
    RenderOwner,
    RenderRegistry,
    RewriteFacade,
)

KManifestPath = PathInfo(__file__).resolve().parent / "ProgramManifest.py"


def ParseArgs() -> Argparse.Namespace:
    Parser = Argparse.ArgumentParser()
    Parser.add_argument("source_root", type=PathInfo)
    Parser.add_argument("--program-root", type=PathInfo, required=True)
    Parser.add_argument("--manifest", type=PathInfo, default=KManifestPath)
    return Parser.parse_args()


def WriteText(Target: PathInfo, Text: str) -> None:
    Target.parent.mkdir(parents=True, exist_ok=True)
    Target.write_text(Text, encoding="utf-8", newline="\n")


def Main() -> int:
    Arguments = ParseArgs()
    Programs = LoadPrograms(Arguments.source_root.resolve())
    if len(Programs) != 1:
        raise ValueError("one independently recovered family is required")
    Program = Programs[0]
    Root = Arguments.program_root.resolve()
    Catalogs, Methods = BuildMethods(Programs)
    NewOwnerCount = 0
    for GroupPath, OwnerSites in Catalogs.items():
        Target = Root / "Owners" / (GroupPath + ".py")
        if Target.exists():
            Existing = ReadAssigns(AstLib.parse(Target.read_text()))["KOwnerSites"][1]
            if not dict(OwnerSites).items() <= Existing.items():
                raise ValueError(f"existing owner catalog is incompatible at {GroupPath}")
        else:
            WriteText(Target, RenderOwner(OwnerSites))
            NewOwnerCount += len(OwnerSites)
    ModelItems = Methods[Program.VariantPath]
    ModulePaths: list[str] = []
    for Method in ModelItems:
        Target = (
            Root
            / Program.VariantPath
            / "Methods"
            / (Method.GroupPath + ".py")
        )
        WriteText(
            Target,
            RenderMethod(
                "convert.adapters.solidworks.programs.Owners."
                + Method.GroupPath.replace("/", "."),
                Method,
            ),
        )
        ModulePaths.append(
            "convert.adapters.solidworks.programs."
            + Program.VariantPath.replace("/", ".")
            + ".Methods."
            + Method.GroupPath.replace("/", ".")
        )
    Facade = RewriteFacade(Program)
    WriteText(
        Root / Program.VariantPath / "Registry.py",
        RenderRegistry(Program, tuple(ModulePaths)),
    )
    WriteText(Root / Program.VariantPath / "Program.py", Facade)
    ManifestPath = Arguments.manifest.resolve()
    Text = ManifestPath.read_text(encoding="utf-8")
    Values = ReadAssigns(AstLib.parse(Text))
    GlobalStats = Values["KGlobalStats"][1]
    GlobalStats = (
        GlobalStats[0] + 1,
        GlobalStats[1] + len(Program.Streams),
        len(tuple((Root / "Owners").rglob("*.py"))),
        GlobalStats[3] + NewOwnerCount,
        GlobalStats[4] + len(ModelItems),
        GlobalStats[5] + sum(len(Operations) for _, Operations in Program.Streams),
    )
    Entry = BuildStat(Program, {Program.VariantPath: Facade})
    PriorTotal = Values["KGlobalStats"][1]
    Text = Text.replace(
        f"KGlobalStats = {PriorTotal!r}", f"KGlobalStats = {GlobalStats!r}", 1
    )
    End = Text.rfind("\n)")
    if End < 0:
        raise ValueError("program manifest does not close its registry")
    Text = Text[:End] + "    " + repr(Entry) + ",\n)" + Text[End + 2 :]
    WriteText(ManifestPath, Text)
    print(
        JsonData.dumps(
            {
                "Catalogs": GlobalStats[2],
                "Methods": GlobalStats[4],
                "Operations": GlobalStats[5],
                "Owners": GlobalStats[3],
                "Programs": GlobalStats[0],
                "Streams": GlobalStats[1],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(Main())
