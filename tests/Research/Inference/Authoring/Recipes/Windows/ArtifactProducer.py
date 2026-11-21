# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson
from importlib import import_module as ImportModule
from typing import Callable, cast as CastValue
from pathlib import Path as FilePath
from sys import argv as ArgValues, path as ImportPaths
from time import monotonic as ReadClock, sleep as SleepBriefly

ImportPaths.insert(0, str(FilePath(__file__).resolve().parents[6] / "re/automation"))

# artifact publication keeps the real runtime store behind its actual process boundary
KArtifacts = CastValue(
    Callable[[FilePath], object], getattr(ImportModule("Artifacts"), "Artifacts")
)


# concurrent real producers must meet at publication without replacing another producer or borrowing native success
def PublishInput() -> None:
    StorePath, InputPath, ReadyPath, ReleasePath = map(FilePath, ArgValues[1:])
    Objects = KArtifacts(StorePath)
    ReadyPath.touch(exist_ok=False)
    Deadline = ReadClock() + 20
    while not ReleasePath.is_file():
        if ReadClock() >= Deadline:
            raise TimeoutError("publication barrier was not released")
        SleepBriefly(0.01)
    PutFile = CastValue(Callable[[FilePath], str], getattr(Objects, "put_file"))
    VerifyBytes = CastValue(Callable[[str], int], getattr(Objects, "verify"))
    Digest = PutFile(InputPath)
    print(EncodeJson({"sha256": Digest, "size_bytes": VerifyBytes(Digest)}))


if __name__ == "__main__":
    PublishInput()
