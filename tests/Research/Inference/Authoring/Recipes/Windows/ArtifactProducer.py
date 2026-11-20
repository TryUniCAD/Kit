# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import dumps as EncodeJson
from pathlib import Path as FilePath
from sys import argv as ArgValues, path as ImportPaths
from time import monotonic as ReadClock, sleep as SleepBriefly

ImportPaths.insert(0, str(FilePath(__file__).resolve().parents[6] / "re/automation"))

from Artifacts import Artifacts


# concurrent real producers must meet at publication without replacing another producer or borrowing native success
def PublishInput() -> None:
    StorePath, InputPath, ReadyPath, ReleasePath = map(FilePath, ArgValues[1:])
    Objects = Artifacts(StorePath)
    ReadyPath.touch(exist_ok=False)
    Deadline = ReadClock() + 20
    while not ReleasePath.is_file():
        if ReadClock() >= Deadline:
            raise TimeoutError("publication barrier was not released")
        SleepBriefly(0.01)
    Digest = Objects.put_file(InputPath)
    print(EncodeJson({"sha256": Digest, "size_bytes": Objects.verify(Digest)}))


if __name__ == "__main__":
    PublishInput()
