from hashlib import sha256
from json import dumps, loads
from pathlib import Path
from subprocess import Popen
from sys import argv, executable, path
from time import monotonic, sleep

path.insert(0, str(Path(__file__).resolve().parents[1]))

from ApplicationWorkers.WindowsIdentity import process_start
from InferenceGrid.Authoring.SolidRoutine import RequestRoutine


def Serve(queue):
    import os

    ready = {"revision": "a" * 40, "pid": os.getpid(), "created": 1,
             "listener": os.getpid(), "listener_created": process_start(os.getpid())}
    (queue / "ready.json").write_text(dumps(ready))
    until = monotonic() + 15
    while monotonic() < until:
        for request in queue.glob("*.request.json"):
            packet = loads(request.read_bytes())
            response = {"status": "completed", "revision": packet["revision"], "sha256": packet["sha256"], "pid": ready["pid"], "created": ready["created"]}
            temporary = queue / "reply.tmp"
            temporary.write_text(dumps(response))
            temporary.rename(request.with_name(request.name.replace(".request.json", ".response.json")))
            return
        sleep(0.01)
    raise TimeoutError("transport request not received")


def Check(directory):
    queue = directory / "Queue" / ("b" * 32)
    queue.mkdir(parents=True)
    (queue.parent / "Active.json").write_text(dumps({"generation": queue.name}))
    manifest = directory / "BatchManifest.json"
    manifest.write_text('{}')
    child = Popen([executable, "-B", __file__, "serve", str(queue)])
    try:
        until = monotonic() + 10
        while not (queue / "ready.json").exists():
            if monotonic() >= until or child.poll() is not None:
                raise TimeoutError("transport listener not ready")
            sleep(0.01)
        host = {"routine_queue": str(queue.parent), "phase_seconds": 10}
        result = RequestRoutine(manifest, host, "a" * 40)
        assert result["sha256"] == sha256(manifest.read_bytes()).hexdigest()
        assert child.wait(timeout=10) == 0
        try:
            RequestRoutine(manifest, host, "a" * 40)
        except TimeoutError:
            pass
        else:
            raise AssertionError("dead owner accepted a second request")
        try:
            RequestRoutine(manifest, host, "c" * 40)
        except ValueError:
            pass
        else:
            raise AssertionError("stale source revision accepted")
    finally:
        if child.poll() is None:
            child.terminate()
            child.wait(timeout=10)
    print("transport custody and stopped owner checks passed")


if __name__ == "__main__":
    Serve(Path(argv[2])) if argv[1] == "serve" else Check(Path(argv[2]))
