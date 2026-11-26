from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import convert
from CheckVertexCase import check_case
from CheckVertexFaults import check_faults


def measure(output):
    assert Path(convert.__file__).resolve().is_relative_to(ROOT / "src"), "SDK must be installed from the candidate checkout"
    manifest_path = ROOT / "re/solidworks/Fixtures/PartitionVertices/Manifest.json"
    raw = manifest_path.read_bytes()
    manifest = json.loads(raw)
    assert manifest["schema"] == "kit.test.current-partition-vertices.v1"
    records = {}
    for case in manifest["cases"]:
        assert not Path(case["path"]).is_absolute() and ".." not in Path(case["path"]).parts
        records[case["role"]] = check_case(ROOT, case, output)
    five, = (item for item in manifest["cases"] if item["role"] == "FiveLine")
    faults = check_faults(ROOT, five)
    assert manifest_path.read_bytes() == raw
    assert not any(name == "pythoncom" or name.startswith("win32com") for name in sys.modules)
    return {"schema": "kit.test.public-active-vertices.v1", "manifest_sha256": sha256(raw).hexdigest(),
            "public_cases": len(records), "cases": records, "faults": faults,
            "legacy_successes_preserved": sum(item["legacy_success_preserved"] for item in records.values()),
            "repaired_topology": records["FiveLine"]["geometry"]["topology"], "native_launches": 0}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(measure(parser.parse_args().output), sort_keys=True, separators=(",", ":")))
