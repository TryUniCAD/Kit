# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as ParseJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe

from pytest import mark as MarkValue

from tests.Research.Archives.Comparison.SemanticSession import PrepareSession

# worker subprocesses must use the checkout containing the independently authored protocol controls
KRepoRoot = FilePath(__file__).resolve().parents[4]


# contradictory dependency custody must fail before publishing comparison evidence even with a freshly calculated fingerprint
@MarkValue.parametrize(
    "CaseName",
    (
        "valid-artifact",
        "valid-pending",
        "valid-direct",
        "missing",
        "undeclared",
        "malformed",
        "missing-result",
        "extra-field",
        "invalid-pending",
        "mismatched-direct",
        "stale-fingerprint",
        "duplicate",
        "linked",
        "nonfinite",
    ),
)
def CheckSession(TmpPath: FilePath, CaseName: str) -> None:
    PrepareSession(TmpPath, CaseName)
    Process = RunProcess(
        [
            PythonExe,
            "-B",
            str(KRepoRoot / "re/automation/SemanticComparisonRunner.py"),
            str(TmpPath),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    ResultPath = TmpPath / "result.json"
    if CaseName.startswith("valid-"):
        assert Process.returncode == 0, Process.stderr
        Records = ParseJson(ResultPath.read_bytes())["records"]
        Report = ParseJson((TmpPath / "work/semantic-report.json").read_bytes())
        assert Records["status"] == "equal_observed_graph"
        assert Records["semantic_qualification"] == "unverified"
        assert Records["native_acceptance"] == "not_established"
        assert Records["fingerprint"] == Report["execution"]["fingerprint"]
    else:
        assert Process.returncode == 1, Process.stdout + Process.stderr
        assert "semantic comparison session refused:" in Process.stderr
        assert not ResultPath.exists()
        assert not any((TmpPath / "work").iterdir())
