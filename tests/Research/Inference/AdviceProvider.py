# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as ParseJson
from os import pathsep as PathSeparator
from pathlib import Path as FilePath
from sys import executable as PythonExe

from tests.Research.SupervisorClient import SessionHost


# a separate provider log detects duplicate requests even when the supervisor overwrites an attempt record
def InstallProvider(Harness: SessionHost, TmpPath: FilePath) -> None:
    Provider = TmpPath / "codex"
    _ = Provider.write_text(
        f"#!{PythonExe}\n"
        "import json, pathlib, sys\n"
        "with pathlib.Path(__file__).with_name('Calls').open('a') as log: log.write('called\\n')\n"
        "args = sys.argv[1:]\n"
        "if args[args.index('--model')+1] != 'gpt-6.2-sol' or "
        "'model_reasoning_effort=\"medium\"' not in args: sys.exit(2)\n"
        "prompt = sys.stdin.read()\n"
        "if 'private-design-name' in prompt: sys.exit(3)\n"
        "pathlib.Path(args[args.index('--output-last-message')+1]).write_text("
        "json.dumps(dict(hypothesis='field stores depth', controlled_change='vary depth', "
        "prediction_if_true='field changes', prediction_if_false='field stays fixed')))\n",
        encoding="utf-8",
    )
    Provider.chmod(0o700)
    Harness.Environment["PATH"] = (
        str(TmpPath) + PathSeparator + Harness.Environment["PATH"]
    )


# a proposal can be saved only for the accepted receipt of the same deterministic result
def VerifyReceipt(Harness: SessionHost, JobName: str, State: str) -> None:
    Job = Harness.ReadJob(JobName)
    assert Job["state"] == State
    Result = ParseJson(
        (
            Harness.RootPath
            / "SupervisorState/decoder-advice"
            / str(Job["receipt"])
            / "Advice.json"
        ).read_bytes()
    )
    assert Result["attempts"] == [{"effort": "medium", "status": "proposal"}]
    assert Result["verified_rule"] is False
