# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import subprocess
import sys
from pathlib import Path


# legal ownership variants must be recognized without permitting altered notices to bypass policy
def check_notices(root):
    directory = root / "NoticeChecks"
    directory.mkdir()
    source_root = Path(__file__).resolve().parents[3]
    original = Path(__file__).read_text(encoding="utf-8").split("\n\n", 1)[0]
    current = original.replace("Copyright (c) 2026 Parashell, Odin Glynn-Martin", "Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt")
    body = "\n\n# source validation requires a concrete declaration beyond its legal ownership notice\ndef ReadResult(Value: str) -> str:\n    return Value.strip()\n"
    outcomes = []
    for name, notice, expected in (
        ("OriginalNotice", original, 0),
        ("CurrentNotice", current, 0),
        ("AlteredNotice", original.replace("immediately and permanently", "eventually and temporarily"), 1),
        ("PartialNotice", original.splitlines()[0], 1),
    ):
        path = directory / (name + ".py")
        path.write_text(notice + body, encoding="utf-8")
        process = subprocess.run([sys.executable, "-m", "tools.Steering.SteeringCompliance", str(path)], cwd=source_root, capture_output=True, encoding="utf-8", timeout=30, check=False)
        assert process.returncode == expected, (name, process.stdout, process.stderr)
        if expected:
            assert "CMT001" in process.stdout, process.stdout
        outcomes.append(name)
    return {"legal_notices_accepted": 2, "malformed_notices_rejected": 2, "cases": outcomes}
