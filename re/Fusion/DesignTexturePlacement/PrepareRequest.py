# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
import json
import sys
from hashlib import sha256
from pathlib import Path

from PlacementDesign import prepare
from PlacementRequest import OPEN_SCOPE, SCHEMA, origin_bits, require
from GenerateSemantic import publish


def main():
    parser = argparse.ArgumentParser(
        description="Project strict cuboid Design texture placement with an explicit initialized origin"
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("request", type=Path)
    args = parser.parse_args()
    try:
        require(args.request.suffix.lower() == ".json", "Request destination must end in .json")
        require(
            not args.request.exists() and not args.request.is_symlink(), "Request destination already exists"
        )
        source = args.input.read_bytes()
        request = prepare(source)
        payload = (json.dumps(request, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")
        receipt = {
            "schema": SCHEMA,
            "research_only": True,
            "whole_saved_source_admission": False,
            "source_sha256": sha256(source).hexdigest(),
            "request_sha256": sha256(payload).hexdigest(),
            "wood_origin_bits": origin_bits(request["wood_origin_cm"]).hex(),
            "open_saved_scope": OPEN_SCOPE,
        }
        publish(args.request, payload)
        sys.stdout.buffer.write((json.dumps(receipt, sort_keys=True) + "\n").encode("utf-8"))
    except (OSError, KeyError, TypeError, ValueError, OverflowError, RuntimeError) as error:
        parser.exit(1, f"Design texture placement request refused: {error}\n")


if __name__ == "__main__":
    main()
