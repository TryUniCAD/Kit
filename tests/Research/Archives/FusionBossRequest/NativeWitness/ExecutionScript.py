# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

# the execution contract must reject offline plans before any native runtime import
KExecCheck = """
from pathlib import Path
import sys

sys.path.insert(0, str(Path(sys.argv[1]) / "re/Fusion/Reconstruction/DimensionAuthoring"))
from SourceBossPlan import read_plan

try:
    read_plan(Path("plan.json").resolve(strict=True), sys.argv[2], execution=True)
except ValueError as Failure:
    print(str(Failure), file=sys.stderr)
    raise SystemExit(1) from None
raise AssertionError("offline witness passed native execution validation")
"""
