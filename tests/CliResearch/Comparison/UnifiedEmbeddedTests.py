# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as DecodeJson
from pathlib import Path as FilePath

from pytest import mark as MarkValue

from tests.CliResearch.Comparison.EmbeddedHistory import MakeEmbedded
from tests.CliResearch.ResearchClient import ResearchCli
from tests.Research.Archives.Comparison.SemanticComparisonTests import WriteDocument


# root history must not hide missing component history on either comparison input
@MarkValue.parametrize("MissingSide", ("left", "right"))
def CheckEmbedded(TmpPath: FilePath, MissingSide: str) -> None:
    for SideName in ("left", "right"):
        Document = MakeEmbedded(SideName != MissingSide)
        assert Document.feature_timeline
        Folder = TmpPath / SideName
        Folder.mkdir()
        WriteDocument(Folder / "Part.json", Document)
    Reply = ResearchCli(
        TmpPath, "compare", "left", "right", "--unit", "mm", "-o", "Output"
    )
    assert Reply.returncode == 3, Reply.stderr + Reply.stdout
    Output = TmpPath / "Output"
    Summary = DecodeJson((Output / "summary.json").read_bytes())
    PairRow = Summary["pairs"][0]
    assert PairRow["status"] == "unresolved"
    assert PairRow["unified"] is None
    assert Summary["unified"]["count"] == 0
    assert Summary["unified"]["errors"] == 0
    assert not list((Output / "unified").iterdir())
    assert set(PairRow["unified_exclusions"]) == {MissingSide}
    assert PairRow["unified_exclusions"][MissingSide].startswith(
        "MissingFeatureHistory"
    )
    Report = DecodeJson((Output / PairRow["report"]["path"]).read_bytes())
    assert Report["unified_exclusions"] == PairRow["unified_exclusions"]
    assert Report["semantic_qualification"] == "unverified"
    assert Report["native_acceptance"] == "not_established"
