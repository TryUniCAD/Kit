# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from os import name as PlatformName, pathsep as PathSeparator
from pathlib import Path as FilePath
from sys import executable as PythonExe

from pytest import mark as MarkCase

from tests.Research.Inference.InferenceBoundaryTests import GapReport
from tests.Research.Inference.InferenceHost import PrepareWorker
from tests.Research.SupervisorClient import FixtureJob


# a separate provider process observes which credentials and research data cross the boundary
@MarkCase.skipif(PlatformName != "posix", reason="Advice requires POSIX")
@MarkCase.parametrize(
    "Provider,Auth",
    (("codex", "login"), ("codex", "api"), ("claude", "login"), ("claude", "api")),
)
def CheckAuthModes(TmpPath: FilePath, Provider: str, Auth: str) -> None:
    Harness = PrepareWorker(TmpPath)
    ExePath = TmpPath / Provider
    _ = ExePath.write_text(
        f"""#!{PythonExe}
import json, os, pathlib, sys
provider = pathlib.Path(__file__).name
args = sys.argv[1:]
keys = [name for name in ('OPENAI_API_KEY', 'CODEX_API_KEY', 'ANTHROPIC_API_KEY') if name in os.environ]
prompt = sys.stdin.read()
assert 'private-design-name' not in prompt
assert args[args.index('--model') + 1] == 'custom-model'
pathlib.Path(__file__).with_name('AuthKeys.json').write_text(json.dumps(keys))
answer = dict(hypothesis='field stores depth', controlled_change='vary depth', prediction_if_true='field changes', prediction_if_false='field stays fixed')
if provider == 'codex':
    assert '--ephemeral' in args and '--output-schema' in args
    pathlib.Path(args[args.index('--output-last-message') + 1]).write_text(json.dumps(answer))
else:
    assert '--safe-mode' in args and args[args.index('--tools') + 1] == ''
    print(json.dumps(dict(structured_output=answer)))
""",
        encoding="utf-8",
    )
    ExePath.chmod(0o700)
    Harness.Environment["PATH"] = (
        str(TmpPath) + PathSeparator + Harness.Environment["PATH"]
    )
    Harness.Environment.update(
        OPENAI_API_KEY="openai-test-key", ANTHROPIC_API_KEY="anthropic-test-key"
    )
    _ = Harness.Environment.pop("CODEX_API_KEY", None)
    Harness.BindBytes(
        "gap-plan",
        EncodeJson(
            GapReport("private-design-name", "needs-distinguishing-evidence")
        ).encode(),
    )
    Harness.SubmitJobs(
        [
            FixtureJob(
                "advice-gap",
                "inference.paired-gap",
                inputs={"plan": "gap-plan"},
                options={"scope": "private-design-name"},
            )
        ]
    )
    _ = Harness.RunCli(
        "run",
        "--idle-seconds",
        "1",
        "--advisor",
        Provider,
        "--auth",
        Auth,
        "--model",
        "custom-model",
        "--advice-calls",
        "1",
    )
    JobRow = Harness.ReadJob("advice-gap")
    assert JobRow["state"] == "waiting_evidence"
    Record = DecodeJson(
        (
            Harness.RootPath
            / "SupervisorState/decoder-advice"
            / str(JobRow["receipt"])
            / "Advice.json"
        ).read_bytes()
    )
    assert (
        Record["provider"],
        Record["auth"],
        Record["status"],
        Record["verified_rule"],
    ) == (Provider, Auth, "proposal", False)
    KeysSeen = DecodeJson((TmpPath / "AuthKeys.json").read_bytes())
    KeyName = "CODEX_API_KEY" if Provider == "codex" else "ANTHROPIC_API_KEY"
    assert KeysSeen == ([KeyName] if Auth == "api" else [])
