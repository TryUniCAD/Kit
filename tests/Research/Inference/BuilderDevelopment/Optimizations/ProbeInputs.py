# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson
from os import environ as ProcessEnv, name as HostName, pathsep as PathSep
from pathlib import Path as FilePath
from shutil import copyfile as CopyFile
from sys import executable as PythonExe
from tests.Research.SupervisorClient import KRepoRoot


# availability markers prevent tests from requiring a real codex installation while the broker owns its fixture process
def ProbeArgs(
    TmpPath: FilePath,
    RunName: str,
    PacketPath: FilePath,
    ModelName: str = "gpt-6.1-terra",
    ActionName: str = "generate",
    AttemptName: str = "Attempt",
    SourceRoot: FilePath = KRepoRoot,
) -> tuple[list[str], dict[str, str]]:
    RunPath = TmpPath / RunName
    RunPath.mkdir(parents=True, exist_ok=True)
    BinPath = TmpPath / "Bin"
    BinPath.mkdir(exist_ok=True)
    MarkerPath = BinPath / ("codex.exe" if HostName == "nt" else "codex")
    if not MarkerPath.exists():
        _ = CopyFile(PythonExe, MarkerPath)
        MarkerPath.chmod(0o700)
    EnvValue = dict(ProcessEnv)
    EnvValue["PATH"] = str(BinPath) + PathSep + EnvValue.get("PATH", "")
    EnvValue["PYTHONDONTWRITEBYTECODE"] = "1"
    ConfigPath = TmpPath / (RunName + ActionName + AttemptName + ".json")
    ConfigValue = {
        "run_root": str(RunPath),
        "packet_path": str(PacketPath),
        "shared_root": str(TmpPath / "Shared"),
        "provider_log": str(TmpPath / "ProviderCalls.jsonl"),
        "model": ModelName,
        "action": ActionName,
        "attempt": AttemptName,
        "source_root": str(SourceRoot),
    }
    _ = ConfigPath.write_text(EncodeJson(ConfigValue), encoding="utf-8")
    return [
        PythonExe,
        "-B",
        str(FilePath(__file__).with_name("RunProbe.py")),
        str(ConfigPath),
    ], EnvValue
