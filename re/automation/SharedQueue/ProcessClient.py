# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import json
import subprocess
import sys
from pathlib import Path


def job(name, **settings):
    value = {
        "id": name,
        "kind": "fixture.decode",
        "inputs": {},
        "rule_version": "rule@1",
        "tool_version": "tool@1",
    }
    value.update(settings)
    return value


class Client:
    def __init__(self, root, maximum=8):
        self.root = root
        root.mkdir(parents=True)
        self.counter = 0
        self.command = [
            sys.executable,
            str(Path(__file__).resolve().parents[1] / "Controller.py"),
            "--store",
            str(root / "State"),
        ]
        self.run("init", "--max-running", str(maximum))

    def write(self, value):
        self.counter += 1
        path = self.root / f"Record-{self.counter}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def run(self, *args, code=0):
        completed = subprocess.run(
            [*self.command, *map(str, args)],
            capture_output=True,
            encoding="utf-8",
            timeout=60,
            check=False,
        )
        assert completed.returncode == code, (
            args,
            completed.returncode,
            completed.stdout,
            completed.stderr,
        )
        return json.loads(completed.stdout) if code == 0 else completed.stderr

    def enqueue(self, request, jobs, *, revision=0, priority=50, code=0):
        path = self.write(
            {
                "queue_version": 1,
                "request": request,
                "revision": revision,
                "priority": priority,
                "jobs": jobs,
            }
        )
        return self.run("enqueue", path, code=code)

    def claim(self, name, pool=None):
        path = self.root / f"{name}.json"
        args = ("--pool", pool) if pool is not None else ()
        result = self.run(
            "claim", "--worker", f"worker:{name}", "--claim-file", path, *args
        )
        return result["job"], path

    def finish(self, lease, *, code=0):
        result = self.write({"observed": "real process boundary"})
        return self.run(
            "finish",
            "--lease",
            lease,
            "--result",
            result,
            "--outcome",
            "completed",
            "--reason",
            "process fixture complete",
            code=code,
        )

    def state(self, name):
        return self.run("status", "--job", name)["jobs"][0]


def race(command, arguments):
    processes = [
        subprocess.Popen(
            [*command, *map(str, args)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
        )
        for args in arguments
    ]
    results = []
    try:
        for process in processes:
            stdout, stderr = process.communicate(timeout=60)
            assert process.returncode == 0, (process.returncode, stdout, stderr)
            results.append(json.loads(stdout))
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=10)
    return results
