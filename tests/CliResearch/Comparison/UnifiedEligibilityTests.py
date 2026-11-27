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

from tests.CliResearch.Comparison.UnifiedIneligible import MakeIneligible
from tests.CliResearch.ResearchClient import ResearchCli
from tests.Research.Archives.Comparison.SemanticComparisonTests import WriteDocument


# equal observed geometry must not promote datum only or inactive model histories
@MarkValue.parametrize(
    "RecordKind,Diagnostic",
    (("DatumOnly", "MissingBodyHistory"), ("SuppressedBody", "IncompleteFeature")),
)
def CheckEligible(TmpPath: FilePath, RecordKind: str, Diagnostic: str) -> None:
    Document = MakeIneligible(RecordKind)
    assert Document.feature_timeline
    for SideName in ("left", "right"):
        Folder = TmpPath / SideName
        Folder.mkdir()
        WriteDocument(Folder / "Part.json", Document)
    Reply = ResearchCli(
        TmpPath, "compare", "left", "right", "--unit", "mm", "-o", "Output"
    )
    assert Reply.returncode == 0, Reply.stderr + Reply.stdout
    Output = TmpPath / "Output"
    Summary = DecodeJson((Output / "summary.json").read_bytes())
    PairRow = Summary["pairs"][0]
    assert PairRow["status"] == "equal_observed_graph"
    assert PairRow["unified"] is None
    assert Summary["unified"]["count"] == 0
    assert Summary["unified"]["errors"] == 0
    assert not list((Output / "unified").iterdir())
    assert set(PairRow["unified_exclusions"]) == {"left", "right"}
    assert all(
        Reason.startswith(Diagnostic)
        for Reason in PairRow["unified_exclusions"].values()
    )
    Report = DecodeJson((Output / PairRow["report"]["path"]).read_bytes())
    assert Report["unified_exclusions"] == PairRow["unified_exclusions"]
