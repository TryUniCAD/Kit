# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as ParseJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from pytest import mark as MarkValue

from tests.Research.Inference.InferenceBoundaryTests import AssertReceipt, InvokeWorker
from tests.Research.Inference.Scope.WriteFixture import WriteFixture


# coherent protocol observations stay parked until independent saved policy evidence exists
@MarkValue.parametrize("Variant", ("positive", "windows-positive", "raw-positive"))
def CheckParkedGrid(TmpPath: FilePath, Variant: str) -> None:
    Originals = WriteFixture(TmpPath, Variant)
    Result = AssertReceipt(TmpPath, InvokeWorker(TmpPath))
    assert Result["outcome"] == "waiting_evidence"
    RecordValues = CastValue(dict[str, object], Result["records"])
    Assessment = CastValue(dict[str, object], RecordValues["assessment"])
    GridValue = CastValue(dict[str, object], Assessment["native_grid"])
    assert GridValue["qualification"] is False
    assert all(
        SourcePath.read_bytes() == Content for SourcePath, Content in Originals.items()
    )
    Packet = ParseJson((TmpPath / "job.json").read_bytes())
    assert GridValue["controller_dependencies"] == Packet["dependencies"]


# all enclosing hashes are rebuilt so mutations reach the actual cross record admission gates
@MarkValue.parametrize(
    "Variant,Diagnostic",
    (
        ("flag-integer", "native extent or resolved participant count differs"),
        ("support-late", "upper end cap of body A"),
        ("support-boolean", "upper end cap of body A"),
        ("support-normal", "upper end cap of body A"),
        ("support-offset", "upper end cap of body A"),
        ("no-removal", "body A differs from bounded box witness"),
        ("birth-substitution", "process birth differs"),
        ("windows-birth", "process birth differs"),
        ("start-missing", "phase start differs"),
        ("start-null", "phase start differs"),
        ("start-boolean", "phase start differs"),
        ("start-early", "phase start differs"),
        ("start-late", "phase start differs"),
        ("reversed-time", "phase chronology differs"),
        ("future-time", "phase chronology differs"),
        ("boolean-time", "phase chronology differs"),
        ("missing-handoff", "exact owned restart handoff"),
        ("handoff-record", "handoff differs from its accepted result"),
        ("handoff-job_id", "exact owned restart handoff"),
        ("handoff-installation", "exact owned restart handoff"),
        ("handoff-host", "exact owned restart handoff"),
        ("handoff-plan_sha256", "exact owned restart handoff"),
        ("handoff-owner", "exact owned restart handoff"),
        ("handoff-reason", "exact owned restart handoff"),
        ("handoff-at", "exact owned restart handoff"),
        ("unexpected-handoff", "phase B cannot require another restart"),
        ("archive-substitution", "phase B archives differ from accepted phase A"),
        ("one-body", "exactly two named solid bodies are required"),
        ("invented-policy", "requires distinct native mode evidence"),
        ("unhealthy-control", "both healthy pinned controls"),
        ("fixture-marker", "belongs to a disposable fixture"),
    ),
)
def CheckGridRefuse(TmpPath: FilePath, Variant: str, Diagnostic: str) -> None:
    Originals = WriteFixture(TmpPath, Variant)
    Process = InvokeWorker(TmpPath)
    assert Process.returncode == 1, Process.stderr
    assert "inference refused:" in Process.stderr and Diagnostic in Process.stderr
    assert not (TmpPath / "result.json").exists()
    assert all(
        SourcePath.read_bytes() == Content for SourcePath, Content in Originals.items()
    )
