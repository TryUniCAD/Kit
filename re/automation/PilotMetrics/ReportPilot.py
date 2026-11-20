# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse as ArgParser
import sqlite3 as SqlStore
import sys as System
from pathlib import Path

System.path.insert(0, str(Path(__file__).resolve().parents[1]))

from FreezePilot import FreezePilot
from Records import canonical as Canonical
from ReplayPilot import ReplayPilot


# one offline command preserves the exact run evidence before independently replaying it
def MainEntry():
    Parser = ArgParser.ArgumentParser(
        description="Freeze and replay actual A15a offline pilot observations"
    )
    Commands = Parser.add_subparsers(dest="command", required=True)
    Freeze = Commands.add_parser("freeze")
    Freeze.add_argument("--run", type=Path, required=True)
    Freeze.add_argument("--output", type=Path, required=True)
    Freeze.add_argument("--until-unix", type=float)
    Freeze.add_argument("--through", type=int)
    Freeze.add_argument("--evidence-manifest", type=Path)
    Freeze.add_argument("--evidence-sha256")
    Replay = Commands.add_parser("replay")
    Replay.add_argument("--snapshot", type=Path, required=True)
    Replay.add_argument("--snapshot-sha256", required=True)
    Replay.add_argument("--store", type=Path)
    Values = Parser.parse_args()
    try:
        if Values.command == "freeze":
            Result = FreezePilot(
                Values.run,
                Values.output,
                Values.until_unix,
                Values.through,
                Values.evidence_manifest,
                Values.evidence_sha256,
            )
        else:
            Result = ReplayPilot(Values.snapshot, Values.snapshot_sha256, Values.store)
        print(Canonical(Result))
        return 0
    except (ValueError, OSError, KeyError, TypeError, SqlStore.Error) as Error:
        print(
            f"offline pilot report refused: {type(Error).__name__}: {Error}",
            file=System.stderr,
        )
        return 1


if __name__ == "__main__":
    System.exit(MainEntry())
