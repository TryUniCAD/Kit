# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
import subprocess
import sys
from pathlib import Path


# the owner launches this entry point from its frozen research checkout
def MainEntry():
    SourceRoot = Path(__file__).resolve().parents[3]
    sys.path[:0] = [str(SourceRoot / "re/automation"), str(SourceRoot / "src")]
    from Pilot.RunObservation import RunObservation

    Parser = argparse.ArgumentParser(
        description="Observe one fixed two week offline pilot with bounded supervisor recovery"
    )
    Parser.add_argument("--directory", type=Path, required=True)
    Arguments = Parser.parse_args()
    try:
        return RunObservation(Arguments.directory)
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.SubprocessError,
    ) as Error:
        Parser.exit(1, f"offline pilot owner refused: {Error}\n")


if __name__ == "__main__":
    raise SystemExit(MainEntry())
