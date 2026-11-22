# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath

from tests.Research.SupervisorClient import InitStore, WriteConfig
from tests.Research.Inference.Authoring.Pipeline.BindNative import BindNative
from tests.Research.Inference.Authoring.Pipeline.BuildRegistry import BuildRegistry
from tests.Research.Inference.Authoring.Pipeline.SubmitFixture import SubmitFixture


# pipeline setup composes input binding registry configuration and controller submission
def PreparePipeline(TmpPath: FilePath, FaultValue: str) -> tuple[FilePath, FilePath]:
    StorePath = TmpPath / "Store"
    Controller = InitStore(StorePath, 4)
    BindNative(TmpPath, StorePath)
    RegistryPath = BuildRegistry(TmpPath)
    ConfigPath = WriteConfig(
        TmpPath, RegistryPath, {"fixture": 1, "decode": 1}, Controller
    )
    SubmitFixture(TmpPath, StorePath, FaultValue)
    return StorePath, ConfigPath
