from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path, PureWindowsPath
import sys

ROOT = Path(__file__).resolve().parents[3]
NATIVE = ROOT / "re/solidworks/measurements/2026/SdkPerpendicularRegistryNative01.json"
ORACLE = {"build": "34.5.2.0604", "product": "SOLIDWORKS 2026 SP05.2",
          "sha256": "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"}
TRANSPORT = (
    ("before", "control-before", "RootTransport01"),
    ("generated", "generated", "RootTransport01"),
    ("reopen", "reopen", "RootTransport01"),
    ("after", "control-after", "RootTransport02"),
)


def load(path, digest=None):
    data = path.read_bytes()
    actual = sha256(data).hexdigest()
    if digest is not None and actual != digest:
        raise ValueError("identity changed for " + path.name)
    return json.loads(data), actual


def phases(packet, receipt, details):
    result = []
    if receipt["process_identities"] != details["identities"] or receipt["phase_receipts"] != details["phase_receipts"]:
        raise ValueError("validated native records differ from the original result")
    for identity, (mode, name, folder) in zip(details["identities"], TRANSPORT, strict=True):
        transport, _ = load(packet / folder / (name + ".json"))
        if (identity["file_version"], identity["sha256"]) != (ORACLE["build"], ORACLE["sha256"]):
            raise ValueError("native runtime changed")
        if transport["status"] != "transport_exited" or transport["transport_returncode"] != 0:
            raise ValueError("successful native phases need a clean host transport")
        result.append({"mode": mode, "passed": True, "open_errors": 0, "open_warnings": 0,
                       "process_id": identity["process_id"], "process_creation_filetime": identity["process_creation_filetime"],
                       "record_sha256": details["phase_receipts"][name],
                       "started_at": datetime.fromisoformat(transport["started_at"]).timestamp(),
                       "finished_at": datetime.fromisoformat(transport["finished_at"]).timestamp()})
    return result


def normalized(packet):
    native, _ = load(NATIVE)
    job, job_sha = load(packet / "Job.json", native["native_packet_sha256"])
    result, result_sha = load(packet / "Inspection/Result.json", native["raw_result_sha256"])
    fixture, fixture_sha = load(packet / "RegistryInput.json", "a70762b23ea28fd0749fb256d41405393b689da69e441a87cd4acf3a92a37bda")
    if (result["passed"] is not True or result["controls_healthy"] is not True
            or native["all_open_errors_and_warnings_zero"] is not True
            or native["rebuilds_passed"] is not True or native["fresh_saved_reopen_passed"] is not True
            or result["packet_sha256"] != job_sha or result["numeric_checks"] != 190):
        raise ValueError("original native evidence did not qualify the disclosed bundle")
    locator = PureWindowsPath(fixture["native_parent"])
    members = []
    for name, row in sorted(job["generated_files"].items(), key=lambda item: item[0] == locator.name):
        if row["encoded_path"] != str(locator.with_name(name)):
            raise ValueError("measured locator or companion changed")
        archive = (packet / "FrozenGenerated" / name).read_bytes()
        if (len(archive), sha256(archive).hexdigest()) != (row["bytes"], row["sha256"]):
            raise ValueError("frozen actual native input changed")
        members.append({"name": name, "bytes": len(archive), "sha256": row["sha256"]})
    return {"written_at": fixture["saved_at"],
            "receipt": {"written_at": fixture["saved_at"], "controls_healthy": True, "passed": True,
                        "schema": "kit.sw2026.planar-assembly-measurement.v1", "oracle": ORACLE, "root": locator.name,
                        "namespace": str(locator.parent), "members": members, "phases": phases(packet, native, result),
                        "packet_sha256": job_sha, "fixture_sha256": fixture_sha, "native_result_sha256": result_sha}}


if __name__ == "__main__":
    packet = Path(sys.argv[1])
    print(json.dumps({"measurement": normalized(packet)}, indent=2, sort_keys=True, allow_nan=False))
