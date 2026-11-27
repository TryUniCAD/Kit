# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from CodexAdvice.SharedBudget import SharedBudget
from Records import canonical


# local operators need explicit recovery without guessing whether an external request stopped
def main():
    parser = argparse.ArgumentParser(
        description="Inspect shared AI advice consumption or recover a stopped provider request"
    )
    parser.add_argument("--state", required=True, type=Path)
    parser.add_argument(
        "--provider", choices=("codex", "claude", "ollama"), required=True
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    recovery = commands.add_parser("recover")
    recovery.add_argument("--request-key", required=True)
    recovery.add_argument("--provider-stopped", action="store_true", required=True)
    args = parser.parse_args()
    try:
        if not (args.state / "Advice.sqlite3").is_file():
            raise ValueError("shared advice state does not exist")
        budget = SharedBudget(args.state, args.provider)
        try:
            result = (
                budget.status()
                if args.command == "status"
                else budget.recover(args.request_key)
            )
        finally:
            budget.close()
        print(canonical(result))
    except (OSError, ValueError, TypeError, sqlite3.Error) as error:
        parser.exit(1, f"shared advice refused: {error}\n")


if __name__ == "__main__":
    main()
