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
import signal
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from CodexAdvice.AdviceOptions import AdviceOptions
from CodexAdvice.Suggest import request_advice

# a disposable executable exercises real process dispatch without a live provider account
PROVIDER = """#!{python}
import json, os, pathlib, sys, time
args = sys.argv[1:]
root = pathlib.Path(__file__).parent
with (root / 'Calls.jsonl').open('a') as stream:
    stream.write(json.dumps({{'event':'start','pid':os.getpid(),'at':time.time()}})+'\\n')
    stream.flush()
if os.environ.get('ADVICE_CRASH'):
    while True: time.sleep(0.1)
time.sleep(float(os.environ.get('ADVICE_DELAY','0.3')))
if os.environ.get('ADVICE_FAIL'): sys.exit(2)
prompt = sys.stdin.read()
if 'private-design-name' in prompt: sys.exit(3)
answer = dict(hypothesis='field stores depth', controlled_change='vary depth', prediction_if_true='field changes', prediction_if_false='field stays fixed')
if os.environ.get('ADVICE_INVALID'): answer['prediction_if_false'] = 'field changes'
pathlib.Path(args[args.index('--output-last-message')+1]).write_text(json.dumps(answer))
with (root / 'Calls.jsonl').open('a') as stream:
    stream.write(json.dumps({{'event':'end','pid':os.getpid(),'at':time.time()}})+'\\n')
"""


# child processes own independent caller evidence while sharing their provider coordination state
def child(args):
    root = args.directory
    destination = root / args.name
    destination.mkdir(mode=0o700)
    options = AdviceOptions(
        "codex",
        "login",
        "gpt-6.2-sol",
        4,
        str(root / "Shared"),
        args.limit,
        args.parallel,
    )
    packet = {
        "model": options.model,
        "question": "Which control distinguishes the field?",
        "discovery_summary": args.summary,
        "private": "private-design-name",
    }
    attempts = []

    # an external marker reproduces prerequisites changing while another caller owns the provider
    def current():
        return not (root / (args.name + ".Stale")).exists()

    result = request_advice(
        str(root / "codex"),
        packet,
        attempts,
        args.seconds,
        destination,
        current,
        ("medium", "xhigh") if args.fallback else ("medium",),
        options,
    )
    (root / (args.name + ".json")).write_text(
        json.dumps({"proposal": result, "attempts": attempts})
    )


# concurrent command invocations reproduce independent supervisors without importing coordinator internals
def start(
    root,
    name,
    summary="ambiguous field",
    *,
    limit=5,
    parallel=1,
    seconds=3,
    fallback=False,
    **env,
):
    args = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--directory",
        str(root),
        "--child",
        "--name",
        name,
        "--summary",
        summary,
        "--limit",
        str(limit),
        "--parallel",
        str(parallel),
        "--seconds",
        str(seconds),
    ]
    if fallback:
        args.append("--fallback")
    return subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, **env},
        text=True,
    )


# scenario roots contain only independently disposable provider and coordinator state
def setup(parent, name):
    root = parent / name
    root.mkdir(mode=0o700)
    executable = root / "codex"
    executable.write_text(PROVIDER.format(python=sys.executable))
    executable.chmod(0o700)
    return root


# process failures must retain diagnostics from the actual public advice entry point
def settle(process, expected=0):
    stdout, stderr = process.communicate(timeout=30)
    assert process.returncode == expected, (stdout, stderr)


# separate invocation logs detect duplicate provider dispatch and concurrency oversubscription
def events(root):
    path = root / "Calls.jsonl"
    return (
        [json.loads(line) for line in path.read_text().splitlines()]
        if path.exists()
        else []
    )


# operational commands must expose charged reservations through their supported process boundary
def command(root, *args):
    result = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).with_name("SharedAdvice.py")),
            "--state",
            str(root / "Shared"),
            "--provider",
            "codex",
            *args,
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    return json.loads(result.stdout)


# provider startup must be observed before testing cancellation or stale evidence
def wait_started(root):
    deadline = time.monotonic() + 10
    while not events(root):
        if time.monotonic() >= deadline:
            raise AssertionError("provider did not start")
        time.sleep(0.05)
    return events(root)[0]["pid"]


# identical concurrent prompts and later callers must consume exactly one provider invocation
def duplicate(parent):
    root = setup(parent, "Duplicate")
    first = start(root, "First")
    second = start(root, "Second")
    settle(first)
    settle(second)
    settle(start(root, "Cached"))
    assert len([row for row in events(root) if row["event"] == "start"]) == 1
    assert all(
        json.loads((root / (name + ".json")).read_text())["proposal"]
        for name in ("First", "Second", "Cached")
    )
    assert command(root, "status")["providers"][0]["used"] == 1
    settle(start(root, "Conflict", limit=6), 1)
    assert command(root, "status")["providers"][0]["call_limit"] == 5


# distinct queued prompts must obey both global allowance and provider concurrency
def capacity(parent):
    root = setup(parent, "Capacity")
    children = [
        start(root, "Call" + str(index), "field " + str(index), limit=2)
        for index in range(3)
    ]
    for process in children:
        settle(process)
    log = events(root)
    active = 0
    for row in log:
        active += 1 if row["event"] == "start" else -1
        assert active in (0, 1)
    assert active == 0 and len(log) == 4
    reports = [
        json.loads((root / ("Call" + str(index) + ".json")).read_text())
        for index in range(3)
    ]
    assert sum(report["proposal"] is not None for report in reports) == 2
    assert any(
        report["attempts"][-1]["status"] == "shared_budget_exhausted"
        for report in reports
    )
    assert command(root, "status")["providers"][0]["used"] == 2
    fallback_root = setup(parent, "Fallback")
    settle(start(fallback_root, "Invalid", limit=1, fallback=True, ADVICE_INVALID="1"))
    report = json.loads((fallback_root / "Invalid.json").read_text())
    assert [row["status"] for row in report["attempts"]] == [
        "invalid_answer",
        "shared_budget_exhausted",
    ]
    assert len([row for row in events(fallback_root) if row["event"] == "start"]) == 1


# changed caller evidence must leave the queue without dispatching another provider request
def stale(parent):
    root = setup(parent, "Stale")
    first = start(root, "Owner", "first field", ADVICE_DELAY="0.8")
    wait_started(root)
    second = start(root, "Waiter", "second field")
    time.sleep(0.15)
    (root / "Waiter.Stale").touch()
    settle(second)
    settle(first)
    report = json.loads((root / "Waiter.json").read_text())
    assert report["proposal"] is None and report["attempts"][-1]["status"] == "stale"
    assert len([row for row in events(root) if row["event"] == "start"]) == 1


# timeouts must stop fallback and retain charged capacity until explicit operator recovery
def timeout(parent):
    root = setup(parent, "Timeout")
    settle(start(root, "Timed", seconds=1, fallback=True, ADVICE_CRASH="1"))
    report = json.loads((root / "Timed.json").read_text())
    assert report["proposal"] is None
    assert [row["status"] for row in report["attempts"]] == [
        "timeout",
        "shared_uncertain",
    ]
    snapshot = command(root, "status")
    assert snapshot["providers"][0]["used"] == 1
    assert snapshot["reservations"][0]["state"] == "uncertain"
    settle(start(root, "Blocked", "other field", seconds=1))
    assert (
        json.loads((root / "Blocked.json").read_text())["attempts"][-1]["status"]
        == "shared_wait_timeout"
    )
    key = snapshot["reservations"][0]["request_key"]
    assert (
        command(root, "recover", "--request-key", key, "--provider-stopped")[
            "budget_refunded"
        ]
        is False
    )
    settle(start(root, "Recovered", "fresh field"))
    settle(start(root, "Prior"))
    assert (
        json.loads((root / "Prior.json").read_text())["attempts"][-1]["status"]
        == "shared_prior_failure"
    )
    assert command(root, "status")["providers"][0]["used"] == 2


# a crashed requester must never make a potentially billed call eligible for automatic replay
def crashed(parent):
    root = setup(parent, "Crashed")
    process = start(root, "Killed", seconds=10, ADVICE_CRASH="1")
    provider_pid = wait_started(root)
    process.kill()
    process.communicate(timeout=5)
    os.kill(provider_pid, signal.SIGKILL)
    snapshot = command(root, "status")
    assert snapshot["providers"][0]["used"] == 1
    assert snapshot["reservations"][0]["state"] == "running"
    settle(start(root, "Duplicate", seconds=1))
    assert (
        json.loads((root / "Duplicate.json").read_text())["attempts"][-1]["status"]
        == "shared_wait_timeout"
    )
    key = snapshot["reservations"][0]["request_key"]
    _ = command(root, "recover", "--request-key", key, "--provider-stopped")
    settle(start(root, "Fresh", "new context"))
    assert command(root, "status")["providers"][0]["used"] == 2
    assert len([row for row in events(root) if row["event"] == "start"]) == 2


# the fixture is one executable integration entry point for the normal shared test suite
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--name")
    parser.add_argument("--summary", default="ambiguous field")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--parallel", type=int, default=1)
    parser.add_argument("--seconds", type=int, default=3)
    parser.add_argument("--fallback", action="store_true")
    args = parser.parse_args()
    if args.child:
        child(args)
        return
    for scenario in (duplicate, capacity, stale, timeout, crashed):
        scenario(args.directory)
    print(json.dumps({"checks": 5, "live_provider_calls": 0}))


if __name__ == "__main__":
    main()
