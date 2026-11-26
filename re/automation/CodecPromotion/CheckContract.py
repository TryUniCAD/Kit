# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import os
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from CodecPromotion.Contract import matches, validate, verify_file
from CodecPromotion.Probe import probe


def main():
    root = Path(__file__).resolve().parents[3]
    os.environ["PYTHONPATH"] = os.pathsep.join(map(str, (root / "src", root / "Cli")))
    os.environ.pop("KIT_CODEC_REFERENCE", None)
    contract = json.loads(Path(sys.argv[1]).read_bytes())
    validate(contract, ())
    for case in contract["cases"]:
        sample = root / case["file"]
        verify_file(sample, case["sha256"])
        values = probe(sample, contract["mode"], contract["target_suffix"], list(case["expect"]))
        if not matches(values, case["expect"].values()):
            raise ValueError("codec regression for " + case["file"])


if __name__ == "__main__":
    main()
