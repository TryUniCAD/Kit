# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
import json
import subprocess
import sys
from pathlib import Path


# direct script entry keeps pilot orchestration outside the production runtime
def MainEntry():
    SourceRoot = Path(__file__).resolve().parents[3]
    sys.path[:0] = [str(SourceRoot / "re/automation"), str(SourceRoot / "src")]
    from Pilot.PrepareRun import PrepareRun

    Parser = argparse.ArgumentParser(
        description="Prepare a fresh models off offline research pilot"
    )
    Parser.add_argument("--directory", type=Path, required=True)
    Parser.add_argument("--source-revision", required=True)
    Parser.add_argument("--sessions", type=int, choices=range(1, 3), default=1)
    Arguments = Parser.parse_args()
    try:
        print(
            json.dumps(
                PrepareRun(
                    Arguments.directory,
                    SourceRoot,
                    Arguments.source_revision,
                    Arguments.sessions,
                ),
                sort_keys=True,
            )
        )
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.SubprocessError,
    ) as Error:
        Details = getattr(Error, "stderr", None)
        if isinstance(Details, bytes):
            Details = Details.decode("utf-8", "replace")
        Parser.exit(1, f"offline pilot preparation refused: {Error}\n{Details or ''}\n")


if __name__ == "__main__":
    MainEntry()
