# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as HashBytes
from json import loads as DecodeJson
from pathlib import Path as FilePath
from pytest import mark as CaseMark

from tests.Research.SupervisorClient import KRepoRoot
from tests.Research.Inference.Authoring.Recipes.PrepareSource import PrepareSource
from tests.Research.Inference.Authoring.Recipes.RunProbe import RunProbe


# native source receipts must bind actual compiler builder and specification bytes at the checked out revision
def CheckSourcePins(TmpPath: FilePath) -> None:
    Process = RunProbe(TmpPath, "source", {})
    assert Process.returncode == 0, Process.stderr
    Manifest = DecodeJson(Process.stdout)
    Paths = {Entry["path"] for Entry in Manifest}
    assert len(Paths) == len(Manifest)
    assert {
        "re/automation/FeatureRecipeSpecs.json",
        "re/automation/InferenceGrid/FeatureSpecs.py",
        "re/automation/CaptureTools/Catalogue/Recipes/CompileRecipe.py",
        "re/automation/CaptureTools/Catalogue/Recipes/RecipeRegistry.py",
        "re/automation/CaptureTools/Catalogue/SolidWorks/Programs/BuildProgram.cs",
    } <= Paths
    for Entry in Manifest:
        Content = (KRepoRoot / Entry["path"]).read_bytes()
        assert Entry["sha256"] == HashBytes(Content).hexdigest()
        assert Entry["size_bytes"] == len(Content)


# queued native execution must reject modified missing or newly added dependencies before native startup
@CaseMark.parametrize("Fault", ("modified", "missing", "extra", "native"))
def CheckSourceGate(TmpPath: FilePath, Fault: str) -> None:
    Original = RunProbe(TmpPath, "source", {})
    assert Original.returncode == 0, Original.stderr
    SourceRoot = PrepareSource(TmpPath, DecodeJson(Original.stdout))
    Clean = RunProbe(TmpPath, "source", {"source_root": str(SourceRoot)})
    assert Clean.returncode == 0, Clean.stderr
    assert DecodeJson(Clean.stdout) == DecodeJson(Original.stdout)
    Target = (
        SourceRoot / "re/automation/CaptureTools/Catalogue/Recipes/CompileRecipe.py"
    )
    if Fault == "native":
        Target = (
            SourceRoot
            / "re/automation/CaptureTools/Catalogue/SolidWorks/Programs/BuildProgram.cs"
        )
    if Fault in {"modified", "native"}:
        _ = Target.write_bytes(Target.read_bytes() + b"\nchanged native source\n")
    elif Fault == "missing":
        Target.unlink()
    else:
        Target = Target.parent / "Nested/Injected.py"
        Target.parent.mkdir()
        _ = Target.write_text(
            "raise RuntimeError('must never execute')\n", encoding="utf-8"
        )
    Rejected = RunProbe(TmpPath, "source", {"source_root": str(SourceRoot)})
    assert Rejected.returncode != 0
    assert not Rejected.stdout.strip()
