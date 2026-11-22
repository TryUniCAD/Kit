from argparse import ArgumentParser
from io import BytesIO
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(HERE.parent), str(ROOT / "src")]

from AuditSavedSweepMain import LOCK, checked, demand
from CheckSavedSweepSdk import RECEIPT_PATH, TOPOLOGY, preload
from convert import open_document
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
from convert.adapters.solidworks.Core.Writing.CanWriteSweep import CanWriteSweep
from SavedSweepReplay import guard_runtime
from SavedSweepSdkModel import compare_model

FIXTURES = ROOT / "re/solidworks/v2026/corpus/saved-sweep/SavedSweepWide01"
MANIFEST_SHA = "54461829abdc7501bcb3e5944adf9d569d345471e748c9e93b2ff77ec400cff4"


def run(role):
    manifest = json.loads(checked(FIXTURES / "Fixtures.json", MANIFEST_SHA))
    expected = manifest["cases"][role]
    demand(manifest["source_lock_sha256"] == LOCK and manifest["source_slot"] == 2
           and manifest["fixture_native_observations"] == manifest["writer_acceptance_credits"] == 0
           and expected["archive_sha256"] != expected["original_archive_sha256"],
           "test fixture must remain distinct from the measured original")
    rows = json.loads(checked(RECEIPT_PATH, TOPOLOGY))["states"]
    source, = (row for row in rows if (row["slot"], row["role"]) == (2, role))
    demand(source["file_sha256"] == expected["original_archive_sha256"]
           and source["native_phase"]["sha256"] == expected["native_phase_receipt_sha256"],
           "fixture topology evidence belongs to another native input")
    spec = json.loads(checked(HERE.with_name("DisclosedSweepInputs.json"), manifest["authored_spec_sha256"]))["cases"][1]
    section = spec["section_radius_m" if role == "original" else "edit_section_radius_m"]
    job = {
        "drivers_m": (2.0 * section, spec["path_radius_m"]),
        "prior": source,
        "native_measurement": {"mass": source["geometry"]["measures"]["native"]},
    }
    raw = checked(FIXTURES / expected["file"], expected["archive_sha256"])
    demand(len(raw) == expected["archive_bytes"], "test archive extent changed")
    preload()
    blocked = guard_runtime()
    adapter = SldprtAdapter()
    direct = adapter.read(raw, ReadOptions(configuration="Default", strict=True))
    normal = open_document(BytesIO(raw), source_format=KPartFormatId, strict=True)
    design = open_document(BytesIO(raw), source_format=KPartFormatId, strict=True,
                           configuration="Default", include_brep=False)
    observed = compare_model(direct, (normal,), design, job)
    demand(direct.source.sha256 == expected["archive_sha256"]
           and design.source.sha256 == expected["archive_sha256"]
           and direct.source.attributes["saved_sweep_result"] is True
           and not CanWriteSweep(normal, BytesIO()) and not CanWriteSweep(design, BytesIO()),
           "actual saved readback lost its source authority or entered the cold writer")
    demand(not blocked and not any(name.startswith(("pythoncom", "win32com")) for name in sys.modules),
           "saved fixture SDK read accessed a runtime file or CAD process")
    return {"role": role, "fixture_sha256": expected["archive_sha256"],
            "native_source_sha256": expected["original_archive_sha256"],
            "strict_reader_routes": 3, "runtime_accesses": len(blocked), "native_launches": 0,
            **observed}


if __name__ == "__main__":
    parser = ArgumentParser(description="Read one scrubbed disclosed sweep at the strict SDK boundary")
    parser.add_argument("--role", choices=("original", "section"), required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.role), sort_keys=True, allow_nan=False))
