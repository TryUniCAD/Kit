"""Compare a vendor-authored blind boss's PMI row with its independent API read."""

from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "re/solidworks/WriterResearch"))
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.Container.Container import SldprtArchive
from ExchangePack import PackExchange
from PartPmiDatabase import AnnotationRecord, PmiLength
from VerifyObjectExchangeDb import LiveRecords


PMI_STREAM = "Contents/PMISemanticDataDB"
INDEX_SCHEMA = "kit.sw2026.vendor-boss-corpus-index.v1"
ROLES = ("NoOpBefore", "NoOpAfter", "CustomText", "ProfileContrast", "DepthContrast")


def verified_bytes(path, expected_digest):
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != expected_digest:
        raise ValueError(f"input digest differs from the index: {path.name}")
    return raw


def compare_case(run_root, role, case, lifetime, oracle):
    source_path = run_root / "Author" / role / "Prism.SLDPRT"
    if case["relative_file"] != f"{role}/Prism.SLDPRT":
        raise ValueError(f"unexpected capture path for {role}")

    native_bytes = verified_bytes(run_root / role / "Record.json", lifetime["record_sha256"])
    native = json.loads(native_bytes.decode("utf-8-sig"))
    identity = native["oracle_identity"]
    if (
        native["role"] != role
        or native["passed"] is not True
        or lifetime["exit_code"] != 0
        or native["open_errors"] != 0
        or native["open_warnings"] != 0
        or identity["build"] != oracle["build"]
        or identity["sha256"] != oracle["sha256"]
        or native["rebuilt"]["depth_m"] != case["depth_m"]
    ):
        raise ValueError(f"native source observation is inconsistent for {role}")

    raw = verified_bytes(source_path, case["archive_sha256"])
    if len(raw) != case["archive_bytes"]:
        raise ValueError(f"archive byte count differs from the index for {role}")
    archive = SldprtArchive.from_bytes(raw, source_path.name)
    records = LiveRecords(archive.require(PMI_STREAM))
    if len(records) != 1:
        raise ValueError(f"unsupported PMI annotation inventory for {role}")
    _, value = records[0]
    typed = PmiLength("D1", "Boss-Extrude1", 0, native["rebuilt"]["depth_m"], True)
    expected = PackExchange(AnnotationRecord(typed, source_path.stem))
    if value != expected:
        raise ValueError(f"PMI value does not match the measured driver for {role}")
    verified_bytes(source_path, case["archive_sha256"])
    return {
        "case": role,
        "archive_sha256": case["archive_sha256"],
        "native_record_sha256": lifetime["record_sha256"],
        "driver_metres": typed.Metres,
        "pmi_value_bytes": len(value),
        "pmi_value_sha256": sha256(value).hexdigest(),
    }


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--index", required=True, type=Path)
    parser.add_argument("--capture", required=True, type=Path)
    arguments = parser.parse_args()
    index_bytes = arguments.index.read_bytes()
    index = json.loads(index_bytes)
    run = index["runs"]["Discovery02"]
    if (
        index["schema"] != INDEX_SCHEMA
        or run["healthy_controls"] is not True
        or set(run["cases"]) != set(ROLES)
    ):
        raise ValueError("requires the indexed, warmed Discovery02 capture")
    report = [
        compare_case(
            arguments.capture, role, run["cases"][role], run["lifetimes"][role], index["oracle"]
        )
        for role in ROLES
    ]
    if arguments.index.read_bytes() != index_bytes:
        raise ValueError("corpus index changed during verification")
    print(json.dumps({
        "index_sha256": sha256(index_bytes).hexdigest(),
        "cases": report,
    }, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (OSError, KeyError, TypeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(3) from error
