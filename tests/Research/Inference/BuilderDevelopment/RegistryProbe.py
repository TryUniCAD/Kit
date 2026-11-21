# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.Security.PathBoundary import ResolveTemp

from json import loads as DecodeJson
from importlib import import_module as ImportModule
from typing import Callable, cast as CastValue
from pathlib import Path as FilePath
from sys import argv as ArgValues, path as SearchPaths

# registry checks must consume receipts from the actual tested checkout
KRepoRoot = FilePath(__file__).resolve().parents[4]

SearchPaths.insert(0, str(KRepoRoot))
SearchPaths.insert(0, str(KRepoRoot / "re/automation"))


# fixture proof must be rejected before any licensed worker can be dispatched
def ProbeRegistry() -> int:
    ValidateCall = CastValue(
        Callable[[dict[str, object], dict[str, object], object], dict[str, object]],
        ImportModule("InferenceGrid.BuilderDevelopment.Registry").ValidateRegistration,
    )
    RootPath = ResolveTemp(ArgValues[1])
    JobValue = DecodeJson((RootPath / "Run/BuilderJob.json").read_bytes())
    Manifest = DecodeJson((RootPath / "Manifest.json").read_bytes())
    try:
        _ = ValidateCall(Manifest, JobValue, Manifest["candidate"])
    except (OSError, ValueError, KeyError, TypeError) as ErrorInfo:
        print(str(ErrorInfo))
        return 2
    print("fixture registration was incorrectly accepted")
    return 0


if __name__ == "__main__":
    raise SystemExit(ProbeRegistry())
