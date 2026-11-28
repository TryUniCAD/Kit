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
import signal
import subprocess
import sys
import time
from pathlib import Path


# real disposable process execution distinguishes active claim recovery from an idle supervisor restart
def MainEntry():
    RootPath = Path(__file__).resolve().parents[3]
    sys.path[:0] = [str(RootPath / "re/automation"), str(RootPath / "src")]
    from Processes import process_start
    from Pilot.PilotExercise import PilotProcess
    from Pilot.PilotFiles import WriteRecord

    Parser = argparse.ArgumentParser(
        description="Exercise the offline pilot through real process boundaries"
    )
    Parser.add_argument("--directory", type=Path, required=True)
    Arguments = Parser.parse_args()
    Client = PilotProcess(RootPath, Arguments.directory.resolve())
    Client.PreparePilot()
    Manifest = json.loads((Client.Directory / "RunManifest.json").read_bytes())
    Registry = json.loads(Path(Manifest["registry"]).read_bytes())
    assert (
        Manifest["model_calls_enabled"] is False
        and Manifest["application_dispatch_enabled"] is False
    )
    assert set(Registry["runners"]) == {
        "inference.fields",
        "inference.paired-gap",
        "inference.rescan",
    }
    assert not (Client.Directory / "Observation.json").exists()
    Interrupted = None
    Client.StartOwner()
    try:
        Client.AwaitEvents("supervisor_started")
        WindowBytes = (Client.Directory / "Observation.json").read_bytes()
        Window = json.loads(WindowBytes)
        assert Window["planned_until"] - Window["started_at"] == 1209600
        BaseArgv = [
            sys.executable,
            "-B",
            str(RootPath / "re/automation/Controller.py"),
            "--store",
            str(Client.Directory / "Store"),
        ]
        UntilTime = time.monotonic() + 120
        while time.monotonic() < UntilTime:
            for SessionPath in (Client.Directory / "State/sessions").glob(
                "*/session.json"
            ):
                Session = json.loads(SessionPath.read_bytes())
                pid, birth = Session["pid"], Session["process_start"]
                if process_start(pid, live=True) != birth:
                    continue
                held = False
                try:
                    if os.name == "posix":
                        try:
                            os.kill(pid, signal.SIGSTOP)
                        except ProcessLookupError:
                            continue
                        held = True
                    Current = json.loads(
                        subprocess.check_output(
                            [*BaseArgv, "status"], cwd=RootPath, timeout=20
                        )
                    )
                    Matching = next(
                        Row for Row in Current["jobs"] if Row["id"] == Session["job_id"]
                    )
                    if (
                        Matching["state"] != "running"
                        or Matching["kind"]
                        not in {"inference.fields", "inference.rescan"}
                        or process_start(pid, live=True) != birth
                    ):
                        continue
                    OwnerInfo = json.loads(
                        (Client.Directory / "OwnerProcess.json").read_bytes()
                    )
                    assert (
                        process_start(OwnerInfo["pid"], live=True) == OwnerInfo["start"]
                    )
                    os.kill(
                        OwnerInfo["pid"],
                        signal.SIGKILL if os.name == "posix" else signal.SIGTERM,
                    )
                    Interrupted = Session
                    break
                finally:
                    if (
                        held
                        and Interrupted is None
                        and process_start(pid, live=True) == birth
                    ):
                        os.kill(pid, signal.SIGCONT)
            if Interrupted is not None:
                break
            assert Client.Owner.poll() is None
            time.sleep(0.05)
        assert Interrupted is not None, "no real active inference worker was observed"
        Client.AwaitEvents("supervisor_started", Minimum=2)
        UntilTime = time.monotonic() + 180
        while time.monotonic() < UntilTime:
            Current = json.loads(
                subprocess.check_output([*BaseArgv, "status"], cwd=RootPath)
            )
            if not any(
                Row["state"] in {"running", "queued"} for Row in Current["jobs"]
            ):
                break
            time.sleep(0.2)
        Recovered = next(
            Row for Row in Current["jobs"] if Row["id"] == Interrupted["job_id"]
        )
        assert Recovered["attempts"] >= 2 and Recovered["state"] == "completed", Current
        assert (
            sum(Row["state"] == "completed" for Row in Current["jobs"]) == 23
        ), Current
        assert (
            sum(Row["state"] == "waiting_evidence" for Row in Current["jobs"]) == 3
        ), Current
        assert process_start(Interrupted["pid"]) != Interrupted["process_start"]
        StartedAt = time.monotonic()
        while time.monotonic() - StartedAt < 66:
            assert Client.Owner.poll() is None
            time.sleep(0.5)
        Heartbeats = Client.AwaitEvents("heartbeat", Minimum=3)
        assert Heartbeats[-1]["supervisor_healthy"] is True
        assert not [
            Entry
            for Entry in Client.ReadEvents()
            if Entry["event"] == "supervisor_stale"
        ]
        assert (
            len(
                [
                    Entry
                    for Entry in Client.ReadEvents()
                    if Entry["event"] == "supervisor_started"
                ]
            )
            == 2
        )
        OwnerInfo = json.loads((Client.Directory / "OwnerProcess.json").read_bytes())
        os.kill(OwnerInfo["pid"], signal.SIGTERM)
        Client.AwaitEvents("supervisor_started", Minimum=3)
        Client.StopOwner()
        (Client.Directory / "Stop.request").unlink()
        Client.StartOwner()
        Client.AwaitEvents("supervisor_started", Minimum=4)
        assert (Client.Directory / "Observation.json").read_bytes() == WindowBytes
        Client.StopOwner()
        ConfigPath = Path(Manifest["config"])
        ConfigPath.write_bytes(ConfigPath.read_bytes() + b" ")
        Refusal = subprocess.run(
            [
                sys.executable,
                "-B",
                str(RootPath / "re/automation/Pilot/RunPilot.py"),
                "--directory",
                str(Client.Directory),
            ],
            cwd=RootPath,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert Refusal.returncode == 1 and "config bytes changed" in Refusal.stderr
        Result = {
            "active_recovery": True,
            "idle_recovery": True,
            "healthy_after_stale_deadline": True,
            "fixed_window_preserved": True,
            "changed_configuration_refused": True,
            "interrupted_job": Interrupted,
            "recovered_job": Recovered,
            "source_revision": Manifest["source_revision"],
        }
        WriteRecord(Client.Directory / "SmokeResult.json", Result)
        print(json.dumps(Result, sort_keys=True))
    finally:
        if os.name == "posix" and Interrupted is not None:
            pid = Interrupted["pid"]
            if process_start(pid, live=True) == Interrupted["process_start"]:
                try:
                    os.kill(pid, signal.SIGCONT)
                except ProcessLookupError:
                    pass
        if Client.Owner is not None:
            Client.StopOwner()


if __name__ == "__main__":
    MainEntry()
