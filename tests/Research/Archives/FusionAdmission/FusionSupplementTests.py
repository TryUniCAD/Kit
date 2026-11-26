# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as DigestBytes
from json import dumps as EncodeJson, loads as ParseJson
from os import environ as ProcessEnv
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe

from pytest import mark as MarkValue

from tests.Research.Archives.FusionAdmission.Checkout import ReplayRepo as ReplayRepo
from tests.Research.Archives.FusionAdmission.Manifest import BuildManifest


# real command refusals preserve the difference between missing custody and verified native observations
@MarkValue.parametrize(
    "CaseName",
    (
        "missing",
        "normalized",
        "bad-verifier",
        "bad-handoff",
        "escape",
        "extra-field",
        "git-environment",
    ),
)
def CheckFusionLane(ReplayRepo: FilePath, TmpPath: FilePath, CaseName: str) -> None:
    Manifest = ParseJson(EncodeJson(BuildManifest(ReplayRepo)))
    Evidence = TmpPath / "Evidence"
    Evidence.mkdir()
    SetFusionMut(Manifest["evidence"][1], Evidence, CaseName)
    Payload = EncodeJson(Manifest, sort_keys=True).encode()
    ManifestPath = TmpPath / "Manifest.json"
    _ = ManifestPath.write_bytes(Payload)
    Environment = dict(ProcessEnv)
    if CaseName == "git-environment":
        Environment["GIT_DIR"] = str(TmpPath / "AbsentGit")
        Environment["GIT_CONFIG_COUNT"] = "1"
        Environment["GIT_CONFIG_KEY_0"] = "core.bare"
        Environment["GIT_CONFIG_VALUE_0"] = "true"
    Result = RunProcess(
        [
            PythonExe,
            "-B",
            str(ReplayRepo / "re/automation/PairedEvidenceManifest.py"),
            "--manifest",
            str(ManifestPath),
            "--manifest-sha256",
            DigestBytes(Payload).hexdigest(),
            "--evidence-root",
            str(Evidence),
        ],
        cwd=ReplayRepo,
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
        env=Environment,
    )
    if CaseName in ("missing", "git-environment"):
        assert Result.returncode == 2, Result.stderr
        Report = ParseJson(Result.stdout)
        assert Report["qualification"] == "not_evaluated"
        assert Report["qualified_pairs"] == 0
        assert [Entry["status"] for Entry in Report["evidence"]] == [
            "waiting_private_evidence"
        ] * 2
    else:
        assert Result.returncode == 1, (Result.stdout, Result.stderr)
        assert "paired evidence preflight refused" in Result.stderr


# each custody fault must alter only the selected evidence input
def SetFusionMut(Fusion: dict[str, object], Evidence: FilePath, CaseName: str) -> None:
    if CaseName == "normalized":
        Selected = Evidence / "fusion"
        Selected.mkdir()
        (Selected / "phase-b").mkdir()
        Content = EncodeJson({"status": "complete", "recipes": {"P01": {}}}).encode()
        _ = (Selected / "phase-b/measurements.json").write_bytes(Content)
        Fusion["input_sha256"] = DigestBytes(Content).hexdigest()
    elif CaseName == "bad-verifier":
        Fusion["verifier_sha256"] = "0" * 64
    elif CaseName == "bad-handoff":
        Fusion["handoff_revision"] = "f" * 40
    elif CaseName == "escape":
        Fusion["input_directory"] = "../fusion"
    elif CaseName == "extra-field":
        Fusion["qualified"] = True
