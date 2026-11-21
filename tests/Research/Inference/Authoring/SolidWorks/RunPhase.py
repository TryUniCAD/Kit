# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from importlib import import_module as ImportModule
from typing import Callable, cast as CastValue
from pathlib import Path
from sys import argv, path

# the child must exercise this checkout rather than an installed research package
KSourceRoot = Path(__file__).resolve().parents[5]

path.insert(0, str(KSourceRoot / "re/automation"))

# native launch diagnostics retain the real research entry point without expanding static import roots
KRunSolidPhase = CastValue(
    Callable[[Path, Path, dict[str, object], str], None],
    getattr(
        ImportModule("CaptureTools.Catalogue.SolidWorks.RunSolidPhase"), "RunSolidPhase"
    ),
)


# an unavailable installation must return native launcher diagnostics through separate process handles
def RunPhase() -> None:
    OutputPath = Path(argv[1])
    KRunSolidPhase(
        OutputPath / "ConfiguredCase.json",
        OutputPath,
        {
            "interop_assembly": str(OutputPath / "MissingInterop.dll"),
            "executable": str(OutputPath / "MissingExecutable.exe"),
            "phase_seconds": 30,
        },
        "first",
    )


if __name__ == "__main__":
    RunPhase()
