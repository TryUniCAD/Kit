# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from GroupSessions import GroupSession
from Sessions import Session, write_private
from Supervisor import Supervisor, read_config
from WindowsJobMembers import has_job_members
from WindowsProcess import WindowsProcess, process_start


def worker(root, bare=False):
    if bare:
        write_private(root / "entered.json", {"pid": os.getpid()})
        time.sleep(60)
        return
    directory = Path(os.environ["KIT_SESSION"])
    metadata = json.loads((directory / "session.json").read_text(encoding="utf-8"))
    assert process_start(metadata["pid"]) == metadata["process_start"]
    child = subprocess.Popen([sys.executable, "-I", "-S", "-c", "import time; time.sleep(60)"])
    write_private(root / "entered.json", {"pid": os.getpid(), "child": child.pid, "metadata": metadata})
    if (directory / "group.json").is_file():
        group = json.loads((directory / "group.json").read_text(encoding="utf-8"))
        paths = [directory / item for item in group["members"]]
    else:
        paths = [directory / "job.json"]
    for path in paths:
        job = json.loads(path.read_text(encoding="utf-8"))
        write_private(path.parent / "result.json", {
            "outcome": "completed", "reason": "held Windows worker observed published process metadata",
            "records": {"count": len(job["inputs"]), "inputs": sorted(job["inputs"]), "tokenless": "lease_token" not in job},
        })


def direct(root, held):
    with open(os.devnull, "wb") as output, open(os.devnull, "wb") as errors:
        process = WindowsProcess(
            [sys.executable, str(Path(__file__).resolve()), "bare-worker", "--root", str(root)],
            root, dict(os.environ), output.fileno(), errors.fileno(), suspended=held,
        )
        try:
            write_private(root / "bootstrap.json", {"pid": process.pid, "identity": process.identity})
            if held:
                sys.stdin.buffer.read(1)
                assert not (root / "entered.json").exists()
            else:
                until = time.monotonic() + 20
                while not (root / "entered.json").is_file():
                    if time.monotonic() >= until:
                        raise AssertionError("eager Windows worker did not enter")
                    time.sleep(0.01)
                assert process.thread is None
            process.signal(9)
            process.wait(10)
            process.finish()
            assert not has_job_members(process.job)
            print(json.dumps({"held": held, "terminated": True}), flush=True)
        finally:
            process.close()


def refused(root, mode):
    host = Supervisor(read_config(root / "Supervisor.json"), True)
    host.acquire()
    host.synchronize()
    path = host.claims / ("launch.group" if mode == "group-stale" else "launch.json")
    if mode == "group-stale":
        claims = host.adapter.ClaimGroup("decode", "launch:fixture", path, {"fixture.decode": 1048576})
        assert len(claims) == 2
        session = GroupSession(host, "decode", claims, path, "launch-proof")
    else:
        claim = host.adapter.ClaimJob("decode", "launch:fixture", path)
        session = Session(host, "decode", claim, path, "launch-proof")
    session.prepare()
    if mode == "metadata-failure":
        (session.directory / "session.json").mkdir()
    elif mode == "stale-owner":
        subprocess.run(host.adapter.command + ["rotate-owner", "--new-owner", "b" * 64], check=True, capture_output=True)
    elif mode == "group-stale":
        changed = root / "Changed.bin"
        changed.write_bytes(b"changed input after grouped staging")
        host.adapter.BindInput("launch:second", changed)
    elif mode == "stale-lease":
        time.sleep(1.2)
    elif mode == "deadline":
        time.sleep(max(0, session.stop_at - time.time()) + 0.05)
    try:
        session.start()
    except (OSError, ValueError) as error:
        assert session.process is not None
        assert session.process.poll() is not None
        assert not has_job_members(session.process.job)
        assert session.process.thread is None
        assert not (root / "entered.json").exists()
        print(json.dumps({"refused": mode, "terminated": True, "reason": str(error)}), flush=True)
    else:
        raise AssertionError("unauthorized Windows worker was released")
    finally:
        if session.process is not None:
            session.process.close()
        for capture in session.logs.values():
            capture.close()
        for descriptor in host.locks:
            os.close(descriptor)


def main():
    parser = argparse.ArgumentParser(description="Real Windows process launch authorization fixture")
    parser.add_argument("operation", choices=("worker", "bare-worker", "held", "eager", "metadata-failure", "stale-owner", "stale-lease", "deadline", "group-stale"))
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    if args.operation in {"worker", "bare-worker"}:
        worker(args.root, args.operation == "bare-worker")
    elif args.operation in {"held", "eager"}:
        direct(args.root, args.operation == "held")
    else:
        refused(args.root, args.operation)


if __name__ == "__main__":
    main()
