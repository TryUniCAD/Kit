# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from importlib import import_module as ImportModule
from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath
from typing import Callable, cast as CastValue
from tests.Research.Inference.BuilderDevelopment.Contracts.ReadRecord import ReadRecord


# worker fixtures use the actual configuration builder while avoiding unrelated host resource reservations
def ConfigWorker(
    RunPath: FilePath, RepoRoot: FilePath, HostPath: FilePath
) -> tuple[FilePath, dict[str, str]]:
    MakeConfig = CastValue(
        Callable[[FilePath, FilePath, FilePath], tuple[FilePath, dict[str, str]]],
        ImportModule("InferenceGrid.BuilderDevelopment.Queue").DevelopmentConfig,
    )
    ConfigPath, ResourceMap = MakeConfig(RunPath, RepoRoot, HostPath)
    ConfigValue = ReadRecord(DecodeJson(ConfigPath.read_bytes()))
    ConfigValue["reserved_cpus"] = 0
    ConfigValue["reserved_memory_mib"] = 0
    _ = ConfigPath.write_text(EncodeJson(ConfigValue), encoding="utf-8")
    return ConfigPath, ResourceMap
