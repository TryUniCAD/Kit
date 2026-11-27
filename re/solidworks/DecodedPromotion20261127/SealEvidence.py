import hashlib
import json
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
directory = root / "re/solidworks/DecodedPromotion20261127"
reader_path = directory / "Evidence/ReaderReceipt.json"
reader = json.loads(reader_path.read_text())
history_path = directory / "Evidence/HistoricalReader/Index.json"
history = json.loads(history_path.read_text()) if history_path.exists() else {}
for row in reader["sdk_source_hashes"]:
    path = root / row["path"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
        path = root / history[row["path"]]["retained_path"]
    data = path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == row["sha256"]
    assert len(data) == row["bytes"]
manifest_path = directory / "Manifest.json"
manifest = json.loads(manifest_path.read_text())
manifest["members"] = [
    {"path": str(path.relative_to(directory)),
     "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
     "bytes": path.stat().st_size}
    for path in sorted(directory.rglob("*"))
    if path.is_file() and path != manifest_path and "__pycache__" not in path.parts
]
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
print(json.dumps({"members": len(manifest["members"]), "native_acceptance": False}))
