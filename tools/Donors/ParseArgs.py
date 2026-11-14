from __future__ import annotations

import argparse as Argparse
from collections.abc import Sequence
from pathlib import Path as FilePath


def ParseArgs(ArgValues: Sequence[str] | None = None) -> Argparse.Namespace:
    ParserInfo = Argparse.ArgumentParser(
        description="keep recorded payload debt in production writers from growing"
    )
    _ = ParserInfo.add_argument("--baseline-file", type=FilePath, required=True)
    _ = ParserInfo.add_argument(
        "--update-baseline",
        action="store_true",
        help="lower entries for roots inside the scanned directories when nothing grew",
    )
    _ = ParserInfo.add_argument("PathValues", metavar="PATH", nargs="+")
    return ParserInfo.parse_args(ArgValues)
