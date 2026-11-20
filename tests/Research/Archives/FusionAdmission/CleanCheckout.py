# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from functools import partial as BindCallback
from pathlib import Path as FilePath
from shutil import rmtree as RemoveTree

from tests.Research.Archives.FusionAdmission.RetryReadonly import RetryReadonly


# disposable clone cleanup must remain confined to the fixture that created it
def CleanCheckout(TargetRoot: FilePath, OwnerRoot: FilePath) -> None:
    OwnerPath = OwnerRoot.resolve(strict=True)
    TargetPath = TargetRoot.resolve(strict=True)
    if (
        TargetRoot.is_symlink()
        or TargetPath.parent != OwnerPath
        or TargetPath.name != "Checkout"
    ):
        raise ValueError("clone cleanup must stay inside its owning fixture directory")
    RemoveTree(TargetPath, onerror=BindCallback(RetryReadonly, TargetPath))
