# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from hashlib import sha256 as DigestBytes
from json import dumps as DumpJson
from json import loads as LoadJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe


# pin the independent replay through its public process boundary
def CheckCutState() -> None:
    RepoPath = FilePath(__file__).resolve().parents[4]
    Result = RunProcess(
        [PythonExe, "-B", "re/automation/FusionCutState/VerifyCutState.py"],
        cwd=RepoPath,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert Result.returncode == 0, Result.stderr.decode(errors="replace")
    Report = LoadJson(Result.stdout)
    for CaseValue in Report["cases"].values():
        assert CaseValue["public_guards"]["strict"] == (
            "Native Fusion projection requires a sketch followed by one extrusion"
        )
        CaseValue["public_guards"]["strict"] = "Unknown native Fusion entity class"
    ArchiveBytes = (
        DumpJson(Report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")
    ActualDigest = DigestBytes(ArchiveBytes).hexdigest()
    assert (
        ActualDigest
        == "bba9de1a17ca9035136bb0fba7dd4d3324c301c4efd5d05161ea933e0be5a5df"
    )
