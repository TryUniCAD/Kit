# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath

from tests.Research.SupervisorClient import InitStore, WriteConfig
from tests.Research.Inference.Authoring.Pipeline.BindNative import BindNative
from tests.Research.Inference.Authoring.Pipeline.BuildRegistry import BuildRegistry
from tests.Research.Inference.Authoring.Recipes.SubmitBatch import SubmitBatch


# actual controller and supervisor setup keeps the batch transport checks on the hosted execution boundary
def PrepareBatch(TmpPath: FilePath, Fault: str) -> tuple[FilePath, FilePath]:
    StorePath = TmpPath / "Store"
    Controller = InitStore(StorePath, 4)
    BindNative(TmpPath, StorePath)
    RegistryPath = BuildRegistry(TmpPath)
    Registry = DecodeJson(RegistryPath.read_bytes())
    Runner = Registry["runners"].pop("fixture.capture.catalogue")
    Runner["argv"][2] = str(FilePath(__file__).with_name("BatchCapture.py"))
    RunnerKind = (
        "capture.catalogue.solidworks.batch"
        if Fault == "native-rejected"
        else "fixture.capture.catalogue"
    )
    Registry["runners"][RunnerKind] = Runner
    _ = RegistryPath.write_text(EncodeJson(Registry), encoding="utf-8")
    ConfigPath = WriteConfig(
        TmpPath, RegistryPath, {"fixture": 1, "decode": 2}, Controller
    )
    SubmitBatch(TmpPath, StorePath, Fault)
    return StorePath, ConfigPath
