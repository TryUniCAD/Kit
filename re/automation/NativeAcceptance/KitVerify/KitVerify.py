import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time

import adsk.core

_handlers = []
_stop = threading.Event()
_event = "kit.native.verification"


def Setup():
    endpoint = Path.home() / ".kit/verification/fusion"
    config_path = endpoint / "config.json"
    config_raw = config_path.read_bytes()
    config = json.loads(config_raw)
    root = Path(config["source_root"])
    if not root.is_absolute() or config["version"] != 1 or not config["sources"]:
        raise ValueError("invalid Kit verification installation")
    for relative, expected in config["sources"].items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("Kit verification sources changed; enable the API again")
    sys.path.insert(0, str(root / "re/automation"))
    from NativeAcceptance.ProcessState import Executable
    from NativeAcceptance.Records import WriteJson

    WriteJson(endpoint / "ready.json", {"pid": os.getpid(), "executable": Executable(), "config_sha256": hashlib.sha256(config_raw).hexdigest()})
    return endpoint


class VerifyEvent(adsk.core.CustomEventHandler):
    def __init__(self, endpoint):
        super().__init__()
        self.endpoint = endpoint
        self.running = False

    def notify(self, args):
        if self.running:
            return
        self.running = True
        try:
            from NativeAcceptance.FusionMeasure import FusionMeasure
            from NativeAcceptance.ProcessState import QuitCurrent
            from NativeAcceptance.Records import FileHash, ReadJson, WriteJson

            app = adsk.core.Application.get()
            for path in sorted((self.endpoint / "jobs").glob("*/request.json")):
                work = path.parent
                request = ReadJson(path)
                if request["pid"] != os.getpid() or time.time() >= request["deadline"] or (work / "response.json").exists() or (work / "cancel.json").exists():
                    continue
                if any(document.isModified or document.dataFile is not None for document in app.documents):
                    WriteJson(work / "response.json", {"status": "unavailable", "error": "fresh verification session contains user documents", "nonce": request["nonce"], "pid": os.getpid()})
                    continue
                if request["source"] not in ("source.f3d", "source.f3z") or FileHash(work / request["source"]) != request["source_sha256"]:
                    raise ValueError("native source does not match its verification request")
                result = FusionMeasure(app, work, request)
                WriteJson(work / "response.json", {**result, "nonce": request["nonce"], "pid": os.getpid(), "source_sha256": request["source_sha256"]})
                if not app.documents.count:
                    QuitCurrent()
                break
        finally:
            self.running = False


def run(context):
    endpoint = Setup()
    (endpoint / "jobs").mkdir(mode=0o700, exist_ok=True)
    app = adsk.core.Application.get()
    event = app.registerCustomEvent(_event)
    handler = VerifyEvent(endpoint)
    event.add(handler)
    _handlers.append(handler)
    _stop.clear()

    def Poll():
        while not _stop.wait(0.5):
            app.fireCustomEvent(_event)

    threading.Thread(target=Poll, daemon=True).start()


def stop(context):
    _stop.set()
    adsk.core.Application.get().unregisterCustomEvent(_event)
    _handlers.clear()
