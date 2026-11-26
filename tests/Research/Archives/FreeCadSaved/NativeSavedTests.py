# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as ParseJson
from pathlib import Path as FilePath
from runpy import run_path as RunPath
from subprocess import run as RunProcess
from sys import executable as PythonExe
from typing import cast as CastValue

from pytest import mark as MarkValue

# native saves must remain reproducible without the private oracle installation
KRepoRoot = FilePath(__file__).resolve().parents[4]

# retained controls belong to research custody rather than runtime package data
KFixtureRoot = KRepoRoot / "re/FreeCad/Verification"

# immutable source hashes distinguish real saved controls from authored mutations
KCases = CastValue(
    dict[str, dict[str, object]], RunPath(str(KFixtureRoot / "Cases.py"))["KCases"]
)


# saved native documents must cross the actual public reader in fresh processes
@MarkValue.parametrize("CaseName", tuple(KCases))
def CheckSavedFiles(CaseName: str) -> None:
    Request = dict(KCases[CaseName])
    Request["source"] = str(KFixtureRoot / str(Request["file"]))
    Process = RunProcess(
        [
            PythonExe,
            "-B",
            str(KFixtureRoot / "CheckReadback.py"),
            EncodeJson(Request),
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert Process.returncode == 0, Process.stderr + Process.stdout
    Report = CastValue(dict[str, object], ParseJson(Process.stdout))
    assert Report["sha256"] == Request["sha256"]
    assert Report["source_unchanged"] is True and Report["forbidden_attempts"] == []
    assert Report["native_qualification"] == "not_established"
    assert len(CastValue(list[object], Report["observations"])) == 2
