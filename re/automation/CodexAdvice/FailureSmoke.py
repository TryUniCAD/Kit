# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from CodexAdvice.SharedSmoke import command, events, settle, setup, start


# failed external dispatch remains ambiguous even when the client process has exited
def failure(parent, mode):
    root = setup(parent, mode)
    provider = root / "codex"
    if mode == "LaunchFailure":
        provider.chmod(0o600)
    settle(start(root, "Failed", fallback=True, ADVICE_FAIL="1"))
    report = json.loads((root / "Failed.json").read_text())
    expected = "launch_failed" if mode == "LaunchFailure" else "provider_failed"
    assert [row["status"] for row in report["attempts"]] == [
        expected,
        "shared_uncertain",
    ]
    snapshot = command(root, "status")
    assert snapshot["providers"][0]["used"] == 1
    assert snapshot["reservations"][0]["state"] == "uncertain"
    before = len(events(root))
    settle(start(root, "Blocked", "another context", seconds=1))
    assert len(events(root)) == before
    assert (
        json.loads((root / "Blocked.json").read_text())["attempts"][-1]["status"]
        == "shared_wait_timeout"
    )
    key = snapshot["reservations"][0]["request_key"]
    recovered = command(root, "recover", "--request-key", key, "--provider-stopped")
    assert recovered["budget_refunded"] is False
    assert command(root, "status")["providers"][0]["used"] == 1
    provider.chmod(0o700)
    settle(start(root, "Fresh", "fresh context"))
    assert json.loads((root / "Fresh.json").read_text())["proposal"] is not None
    settle(start(root, "Duplicate"))
    assert (
        json.loads((root / "Duplicate.json").read_text())["attempts"][-1]["status"]
        == "shared_prior_failure"
    )
    assert command(root, "status")["providers"][0]["used"] == 2
    starts = [row for row in events(root) if row["event"] == "start"]
    assert len(starts) == (1 if mode == "LaunchFailure" else 2)


# the public process boundary also records the explicit unsupported platform refusal
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True, type=Path)
    args = parser.parse_args()
    if os.name != "posix":
        result = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).with_name("SharedSmoke.py")),
                "--directory",
                str(args.directory),
                "--child",
                "--name",
                "Unsupported",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        assert result.returncode != 0
        assert "owner-private local POSIX directory" in result.stderr
    else:
        failure(args.directory, "ProviderFailure")
        failure(args.directory, "LaunchFailure")
    print(json.dumps({"failure_fencing": True, "live_provider_calls": 0}))


if __name__ == "__main__":
    main()
