# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as DecodeJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe
from pytest import mark as CaseMark
from tests.Research.SupervisorClient import KRepoRoot


# fixture process transcripts distinguish real protocol behavior from model or native acceptance claims
@CaseMark.parametrize(
    "ModeName,Status",
    [
        ("success", "candidate"),
        ("timeout", "provider_timeout"),
        ("oversized", "provider_output_limit"),
        ("tools", "provider_tools_forbidden"),
        ("wrongmodel", "provider_policy_failed"),
        ("personal", "provider_instruction_scope_missing"),
        ("personalallowed", "candidate"),
        ("descendant", "candidate"),
        ("cancel", "provider_closed"),
    ],
)
def CheckSession(TmpPath: FilePath, ModeName: str, Status: str) -> None:
    ScriptPath = FilePath(__file__).with_name("SessionProbe.py")
    ResultInfo = RunProcess(
        [PythonExe, "-B", str(ScriptPath), ModeName, str(TmpPath)],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert ResultInfo.returncode == 0, ResultInfo.stdout + ResultInfo.stderr
    Report = DecodeJson(ResultInfo.stdout)
    assert Report["owned_tree_closed"] is True
    assert Report["results"][0]["status"] == Status
    assert Report["elapsed_seconds"] < 15
    if ModeName == "personal":
        Calls = [
            DecodeJson(LogLine)
            for LogLine in (TmpPath / "Calls.jsonl").read_text().splitlines()
        ]
        assert not [
            Value
            for Value in Calls
            if Value.get("request", {}).get("method") == "turn/start"
        ]
    if Status == "candidate":
        assert len(Report["results"]) == 2
        assert Report["results"][1]["capture"]["session_reused"] is True
        assert (
            Report["results"][0]["capture"]["owned_server_pid"]
            == Report["results"][1]["capture"]["owned_server_pid"]
        )
        assert (
            Report["results"][0]["capture"]["ephemeral_thread"]
            != Report["results"][1]["capture"]["ephemeral_thread"]
        )
        assert Report["results"][1]["usage"]["total_tokens"] == 152
        Calls = [
            DecodeJson(LogLine)
            for LogLine in (TmpPath / "Calls.jsonl").read_text().splitlines()
        ]
        assert (
            len(
                [
                    Value
                    for Value in Calls
                    if Value.get("request", {}).get("method") == "initialize"
                ]
            )
            == 1
        )
        assert (
            len(
                [
                    Value
                    for Value in Calls
                    if Value.get("request", {}).get("method") == "thread/unsubscribe"
                ]
            )
            == 2
        )
