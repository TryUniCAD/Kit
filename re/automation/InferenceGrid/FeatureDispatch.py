# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
from pathlib import Path
import sqlite3
import subprocess
import sys

sys.path[:0] = [
    str(Path(__file__).resolve().parents[1]),
    str(Path(__file__).resolve().parents[3] / "src"),
]

from Corpus import git
from InferenceGrid.FeatureAdvance import AdvanceEvidence, ReadAssessment
from InferenceGrid.Provision import ROOT, ProvisionScope
from Ledger import Ledger
from Records import bounded, canonical, label

# the catalogue stable id selects the existing p04 body selection discovery scope
CutExtrude = "family:extrude:cut-extrude"


# the planner dispatches only explicitly supported catalogue identities
def MainDispatch():
    parser = argparse.ArgumentParser(
        description="Dispatch a mapped SOLIDWORKS catalogue feature"
    )
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--feature", choices=(CutExtrude,), required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("submit")
    commands.add_parser("status")
    advance = commands.add_parser("advance")
    advance.add_argument("--config", type=Path, required=True)
    advance.add_argument("--kind", required=True)
    advance.add_argument("--resource", required=True)
    advance.add_argument("--wait-seconds", type=int, default=0)
    args = parser.parse_args()
    try:
        if args.command == "submit":
            revision = git(ROOT, "rev-parse", "HEAD").decode("ascii").strip()
            result = ProvisionScope(args.store, revision)
        elif args.command == "advance":
            result = AdvanceEvidence(
                args.store,
                args.config,
                label(args.kind),
                label(args.resource),
                bounded(args.wait_seconds, 0, 3600),
            )
        else:
            with Ledger(args.store) as ledger:
                result, _ = ReadAssessment(ledger)
        print(canonical({"feature": args.feature, **result}))
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        RuntimeError,
        sqlite3.Error,
        subprocess.SubprocessError,
    ) as error:
        parser.exit(1, f"catalogue feature dispatch refused: {error}\n")


if __name__ == "__main__":
    MainDispatch()
