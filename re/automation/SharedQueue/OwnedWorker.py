# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
import os
import signal
import sys
import time
from pathlib import Path


def main():
    session = Path(sys.argv[1])
    packet = json.loads((session / "job.json").read_text(encoding="utf-8"))
    marker = Path(packet["job"]["options"]["marker"])

    def stopped(signum, frame):
        marker.with_suffix(".stopped").write_text(str(os.getpid()), encoding="ascii")
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, stopped)
    marker.write_text(json.dumps({"pid": os.getpid(), "job": packet["job"]["id"]}), encoding="utf-8")
    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        time.sleep(0.1)
    raise SystemExit("supervisor failed to cancel owned fixture worker")


if __name__ == "__main__":
    main()
