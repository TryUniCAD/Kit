# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe
from pytest import mark as CaseMark
from tests.Research.SupervisorClient import KRepoRoot
from tests.Research.Inference.BuilderDevelopment.RecordDigest import RecordDigest
from tests.Research.Inference.BuilderDevelopment.RunBuilder import RunBuilder
from tests.Research.Inference.BuilderDevelopment.StoreJob import StoreJob
from tests.Research.Inference.BuilderDevelopment.WriteInputs import WriteInputs


# genuine discovery receipts and stale scope hashes must never become native qualification
@CaseMark.parametrize("IsStale", [False, True])
def CheckRegistry(TmpPath: FilePath, IsStale: bool) -> None:
    WriteInputs(TmpPath)
    Prepared = RunBuilder(TmpPath)
    assert Prepared.returncode == 0, Prepared.stdout + Prepared.stderr
    JobValue = DecodeJson((TmpPath / "Run/BuilderJob.json").read_bytes())
    Candidate = {
        "schema": 1,
        "operation": "offset_plane",
        "support": "XY",
        "scale": 1.0,
        "reverse": False,
    }
    InputsValue = {
        "job": JobValue,
        "candidate": Candidate,
        "cases": JobValue["discovery_cases"],
    }
    NativeSpec = {
        "id": "fixture-native",
        "kind": "builder.native",
        "tool_version": JobValue["source_revision"],
        "rule_version": "fixture@1",
        "inputs": InputsValue,
    }
    Native = StoreJob(
        TmpPath,
        NativeSpec,
        "completed",
        {"fixture_only": True, "native_verified": False},
    )
    VerifySpec = {
        **NativeSpec,
        "id": "fixture-verifier",
        "kind": "builder.verify",
        "inputs": {"job": JobValue, "candidate": Candidate, "expectations": {}},
    }
    Verdict = StoreJob(
        TmpPath,
        VerifySpec,
        "completed",
        {"fixture_only": True, "verified": True, "native_verified": False},
    )
    ScopeValue = {
        Field: JobValue[Field]
        for Field in (
            "feature",
            "recipe_sha256",
            "application_build",
            "application_fingerprint",
            "supported_options",
            "parameter_domain",
        )
    }
    if IsStale:
        ScopeValue["application_fingerprint"] = "0" * 64
    Manifest: dict[str, object] = {
        "schema_version": 1,
        "candidate": Candidate,
        "candidate_sha256": RecordDigest(Candidate),
        "scope": ScopeValue,
        "registry_root": str(TmpPath / "Registry"),
        "proof": {
            "directory": str(TmpPath / "Run"),
            "native_job": Native["id"],
            "verification_job": Verdict["id"],
            "native_result_sha256": Native["result"],
            "verification_result_sha256": Verdict["result"],
            "expectations": {},
        },
    }
    Manifest["id"] = RecordDigest(Manifest)
    _ = (TmpPath / "Manifest.json").write_text(EncodeJson(Manifest), encoding="utf-8")
    Process = RunProcess(
        [
            PythonExe,
            "-B",
            str(FilePath(__file__).with_name("RegistryProbe.py")),
            str(TmpPath),
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=40,
    )
    assert Process.returncode == 2, Process.stdout + Process.stderr
    Expected = "incompatible" if IsStale else "reserved qualification stage"
    assert Expected in Process.stdout, Process.stdout + Process.stderr
    assert not (TmpPath / "Run/NativeAttempts").exists()
