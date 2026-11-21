# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from importlib import import_module as ImportModule
from pathlib import Path as FilePath
from sys import path as ImportPaths
from unittest.mock import DEFAULT, patch as Patch


# requesting a real pause before the supervisor starts removes scheduler timing from this control
def PauseDispatch(
    Directory: FilePath,
    SourceRoot: FilePath,
    *Arguments: object,
    **Options: object,
) -> object:
    Runtime = ImportModule("InferenceGrid.CatalogueRuntime")
    assert Runtime.PauseCatalogue(Directory, SourceRoot, None)["status"] == "pausing"
    return DEFAULT


if __name__ == "__main__":
    ImportPaths.insert(
        0, str(FilePath(__file__).resolve().parents[4] / "re/automation")
    )

    # the cli establishes its research import paths before loading the batch runner
    KLauncher = ImportModule("InferenceGrid.RunFeatureCatalogue")

    with Patch(
        "InferenceGrid.CatalogueBatch.RunSupervisor",
        side_effect=PauseDispatch,
        wraps=ImportModule("InferenceGrid.CatalogueBatch").RunSupervisor,
    ):
        raise SystemExit(KLauncher.MainRun())
