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

import convert
from convert.adapters.Fusion.Bridge.CheckContract import CheckContract
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument

from BindingRequest import OPEN_SCOPE, extract, require
from GenerateSemantic import publish


def open_saved(source):
    public = convert.open_document(source, source_format="f3d")
    require(
        public.metadata.get("fusion.read_only") is True, "Input must follow the strict saved-profile route"
    )
    model = ReadDocument(source)
    require(
        CheckContract(public.metadata.get("fusion.native_state"), "model", Version=2) == model,
        "Strict readback does not contain the complete saved profile",
    )
    return model, public


def prepare(source):
    return extract(*open_saved(source))


def main():
    parser = argparse.ArgumentParser(
        description="Project strict saved cuboid parameters into a bounded research request"
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
        publish(args.request, payload)
        receipt = {
            "schema": 1,
            "research_only": True,
            "whole_saved_source_admission": False,
            "source_sha256": sha256(source).hexdigest(),
            "request_sha256": sha256(payload).hexdigest(),
            "parameter_order": request["parameter_order"],
            "retained_material": "label_density_rgba_only",
            "open_saved_scope": OPEN_SCOPE,
        }
        sys.stdout.buffer.write((json.dumps(receipt, sort_keys=True) + "\n").encode("utf-8"))
    except (OSError, KeyError, TypeError, ValueError, OverflowError, RuntimeError) as error:
        parser.exit(1, f"Saved cuboid request refused: {error}\n")


if __name__ == "__main__":
    main()
