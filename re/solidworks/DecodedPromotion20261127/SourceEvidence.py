from hashlib import sha256
import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(root / "src"), str(root / "re/solidworks/WriterResearch")]
from VerifyConfigRoot import CAPTURE_REVISION, principal_captures
from VerifyBossEndOpen import inspect_end_open
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

rows = []
for _, asset, data, _, measurement in principal_captures():
    if not Path(asset["path"]).name.startswith("P03-"):
        continue
    archive = SldprtArchive.from_bytes(data, Path(asset["path"]).name)
    result = inspect_end_open(archive, measurement, False)
    row = {"source_path": asset["path"], "source_sha256": sha256(data).hexdigest(), "measurement_sha256": sha256(json.dumps(measurement, sort_keys=True, separators=(",", ":")).encode()).hexdigest(), "measured_observation": measurement, "packaged_direction_reverse": result[8], "end_interval_sha256": result[9]}
    try:
        ReadNativeLink(archive, 0)
        row["main_typed_link"] = {"status": "returned"}
    except Exception as error:
        row["main_typed_link"] = {"status": "refused", "exception": type(error).__name__, "message": str(error)}
    rows.append(row)
print(json.dumps({"source_revision": CAPTURE_REVISION, "sdk_revision": "91a73de348894a5791a51b977cd6fe0fe677a617", "source_evidence_program_sha256": sha256(Path(__file__).read_bytes()).hexdigest(), "native_calls": 0, "rows": rows}, indent=2))
