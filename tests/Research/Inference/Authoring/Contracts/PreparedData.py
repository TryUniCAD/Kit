# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from pathlib import Path as FilePath
from typing import TypedDict
from tests.Research.Inference.Authoring.Contracts.CompiledCase import CompiledCase


# disk preparation retains native output paths without pretending they are serialized strings
class PreparedData(TypedDict):
    cases: list[CompiledCase]
    outputs: list[FilePath]
    manifest: FilePath
    manifest_sha256: str
    configuration_sha256: list[str]
