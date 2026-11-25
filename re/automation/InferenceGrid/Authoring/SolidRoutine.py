# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
from contextlib import contextmanager
from hashlib import sha256
from json import loads
from os import environ
from pathlib import Path
from time import monotonic, sleep, time
from uuid import uuid4

from CaptureTools.Catalogue.SolidWorks.NativeSolidEnv import NativeSolidEnv
from Records import read_record
from Sessions import write_private


# an application lease belongs to the catalogue rather than an individual short-lived decoder worker
@contextmanager
def OwnSolidRoutine(Directory, SourceRoot, HostPath, Revision):
    from WindowsProcess import WindowsProcess

    Host = read_record(HostPath)
    if Host.get("verification_mode") != "document_reopen":
        yield None
        return
    QueueRoot = Path(Host["routine_queue"])
    if QueueRoot.parent != Directory or QueueRoot.is_symlink():
        raise ValueError("routine queue must belong to its catalogue")
    QueueRoot.mkdir(mode=0o700, exist_ok=True)
    Queue = QueueRoot / uuid4().hex
    Queue.mkdir(mode=0o700)
    Shell = Path(environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    Script = SourceRoot / "re/automation/CaptureTools/Catalogue/SolidWorks/RunSolidWorks.ps1"
    Command = [str(Shell), "-NoProfile", "-NonInteractive", "-STA", "-File", str(Script),
               "-CasePath", str(HostPath), "-OutputDirectory", str(Queue),
               "-InteropAssembly", Host["interop_assembly"], "-ExecutablePath", Host["executable"],
               "-Phase", "first", "-QueueDirectory", str(Queue), "-SourceRevision", Revision]
    with (Queue / "stdout.log").open("xb") as Output, (Queue / "stderr.log").open("xb") as Errors:
        Owner = WindowsProcess(Command, SourceRoot, NativeSolidEnv(Host), Output.fileno(), Errors.fileno())
        try:
            Deadline = monotonic() + 180
            while not (Queue / "ready.json").exists():
                if Owner.poll() is not None or monotonic() >= Deadline:
                    raise RuntimeError(f"SOLIDWORKS routine startup failed; inspect {Queue}")
                sleep(0.1)
            Ready = read_record(Queue / "ready.json")
            if Ready["revision"] != Revision:
                raise ValueError("routine source revision differs")
            Active = QueueRoot / ("Active." + Queue.name + ".tmp")
            write_private(Active, {"generation": Queue.name})
            Active.replace(QueueRoot / "Active.json")
            yield Owner
            if Owner.poll() is not None:
                raise RuntimeError(f"SOLIDWORKS routine owner stopped; inspect {Queue}")
        finally:
            (Queue / "stop").touch(exist_ok=True)
            try:
                if Owner.wait(timeout=45) != 0:
                    raise RuntimeError(f"routine owner cleanup failed; inspect {Queue}")
            finally:
                Owner.close()


# each worker waits for its own immutable manifest while the persistent owner continues serving other batches
def RequestRoutine(Manifest, Host, Revision):
    from ApplicationWorkers.WindowsIdentity import peer_matches

    QueueRoot = Path(Host["routine_queue"]).resolve(strict=True)
    Generation = read_record(QueueRoot / "Active.json")["generation"]
    if not isinstance(Generation, str) or len(Generation) != 32 or any(Char not in "0123456789abcdef" for Char in Generation):
        raise ValueError("invalid routine owner generation")
    Queue = (QueueRoot / Generation).resolve(strict=True)
    if Queue.parent != QueueRoot:
        raise ValueError("routine generation escapes its catalogue")
    Ready = read_record(Queue / "ready.json")
    if Ready["revision"] != Revision or (Queue / "stop").exists():
        raise ValueError("routine owner is stale or stopping")
    Identity = uuid4().hex
    Pin = sha256(Manifest.read_bytes()).hexdigest()
    Deadline = time() + Host.get("phase_seconds", 2400)
    Packet = {"manifest": str(Manifest), "sha256": Pin, "revision": Revision, "deadline": Deadline}
    Temporary = Queue / (Identity + ".tmp")
    write_private(Temporary, Packet)
    Temporary.rename(Queue / (Identity + ".request.json"))
    Response = Queue / (Identity + ".response.json")
    while not Response.exists():
        if time() >= Deadline or (Queue / "stop").exists() or not peer_matches(Ready["listener"], Ready["listener_created"]):
            (Queue / "stop").touch(exist_ok=True)
            raise TimeoutError("routine verification did not complete; owner recovery required")
        sleep(0.05)
    Result = loads(Response.read_bytes())
    if (time() >= Deadline or (Queue / "stop").exists() or Result != {"status": "completed", "revision": Revision, "sha256": Pin,
                   "pid": Ready["pid"], "created": Ready["created"]}
            or sha256(Manifest.read_bytes()).hexdigest() != Pin):
        raise ValueError("routine reply differs from its manifest or owner")
    return Result
