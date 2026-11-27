from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(Path(__file__).resolve().parent), str(ROOT / "re/tooling/sw2026/vertex_read")]

import convert
from AdapterBoundary import assert_fixture, load_fixture
from CheckAttributedFaults import check_faults


def measure():
    assert Path(convert.__file__).resolve().is_relative_to(ROOT / "src")
    folder, manifest, member, native = load_fixture(ROOT)
    active, model, owners, values, volume = assert_fixture(native)
    faults = check_faults(native, active)
    assert (folder / "Manifest.json").read_bytes() == manifest
    assert (folder / "P03ActivePartition.bin").read_bytes() == member
    assert not any(n == "pythoncom" or n.startswith("win32com") for n in sys.modules)
    return {"schema": "kit.test.attributed-active-read.v1", "member_sha256": sha256(member).hexdigest(),
            "manifest_sha256": sha256(manifest).hexdigest(), "topology": [len(model.faces), len(model.edges), len(model.vertices)],
            "signed_volume_mm3": volume, "attribute_owners": owners, "attribute_values": values,
            "face_attributes": {face.id: dict(face.attributes) for face in model.faces}, "faults": faults,
            "all_faults_refused": True, "native_launches": 0,
            "scope": "actual framed member through normal payload extraction and active adapter; no whole-document or native acceptance claim"}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    assert arguments.output.is_dir()
    result = json.dumps(measure(), sort_keys=True, separators=(",", ":")) + "\n"
    (arguments.output / "AttributedRead.json").write_text(result, encoding="utf-8", newline="\n")
    print(result, end="")
