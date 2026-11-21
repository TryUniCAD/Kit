from pathlib import Path
import secrets
import subprocess
import sys
import time

from NativeAcceptance.ProcessState import IsAlive
from NativeAcceptance.Records import Endpoint, FileHash, LockEndpoint, ReadJson, WriteJson


def RunCase(application, work, source, role, availability, configuration=None):
    nonce = secrets.token_hex(24)
    request = {"nonce": nonce, "source": source.name, "source_sha256": FileHash(source), "role": role, "configuration": configuration, "deadline": time.time() + 420}
    if application == "solidworks":
        WriteJson(work / "request.json", request)
        subprocess.run([sys.executable, "-B", str(Path(__file__).with_name("SolidWorksMeasure.py")), str(work)], capture_output=True, timeout=450, check=False)
        if not (work / "response.json").is_file():
            raise ValueError("SOLIDWORKS API worker did not return a native measurement")
        result = ReadJson(work / "response.json")
    else:
        endpoint = Endpoint()
        with LockEndpoint(endpoint / "verification.lock"):
            ready = ReadJson(endpoint / "ready.json")
            if IsAlive(ready["pid"]):
                return {"status": "unavailable", "error": "close Fusion before verification so Kit can launch a fresh owned API session"}
            process = subprocess.Popen([availability["executable"]], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=str(Path(availability["executable"]).parent))
            request["pid"] = process.pid
            WriteJson(work / "request.json", request)
            while not (work / "response.json").is_file():
                if process.poll() is not None or time.time() >= request["deadline"]:
                    WriteJson(work / "cancel.json", {"nonce": nonce, "cancelled": True})
                    raise ValueError("Fusion did not service its API request; enable KitVerify and Run on Startup; the native session was left for owner recovery")
                time.sleep(0.25)
            result = ReadJson(work / "response.json")
            if result.get("pid") != process.pid:
                raise ValueError("Fusion result did not come from the fresh owned process")
            process.wait(timeout=30)
    if time.time() >= request["deadline"] or result.get("nonce") != nonce or result.get("source_sha256") != request["source_sha256"] or FileHash(source) != request["source_sha256"]:
        raise ValueError("native measurement does not bind the unchanged candidate request")
    return result
