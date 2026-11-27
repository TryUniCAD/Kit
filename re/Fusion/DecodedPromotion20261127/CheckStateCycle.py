import hashlib
import json
from pathlib import Path
import sys
import tarfile
import traceback

from convert.adapters.Fusion.Bridge.CheckContract import CheckContract
from convert.Formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument


def main():
    directory = Path(sys.argv[1]).resolve()
    receipt = json.loads((directory / "Receipt.json").read_text())
    results = {"revision": receipt["revision"], "models": False, "native_acceptance": "not_established", "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "source_receipt_sha256": hashlib.sha256((directory / "Receipt.json").read_bytes()).hexdigest(), "rows": []}
    with tarfile.open(directory / "Documents.tar.gz", "r:gz") as archive:
        for row in receipt["rows"]:
            result = {"case": row["case"], "checks": {}}
            try:
                payload = (directory / row["candidate"]).read_bytes()
                state = json.load(archive.extractfile(row["case"] + "/TypedModel.json"))
                decoded_state = CheckContract({"version": 2, "model": state}, "model", 2)
                result["checks"]["state_model_equality"] = decoded_state == ReadDocument(payload)
                emitted = EmitParsed(decoded_state)
                result["checks"]["state_output_hash_equality"] = hashlib.sha256(emitted).hexdigest() == row["candidate_sha256"]
                result["checks"]["state_output_typed_equality"] = ReadDocument(emitted) == decoded_state
                result["status"] = "passed" if all(result["checks"].values()) else "comparison_failed"
            except Exception as error:
                result["status"] = "error"
                result["error"] = str(error)
                result["traceback"] = traceback.format_exc()
            results["rows"].append(result)
            (directory / "StateCycle.json").write_text(json.dumps(results, indent=2, sort_keys=True))
            print(json.dumps(result), flush=True)
    results["summary"] = {"cases": len(results["rows"]), "passed": sum(row["status"] == "passed" for row in results["rows"]), "checks": sum(len(row["checks"]) for row in results["rows"]), "passing_checks": sum(value is True for row in results["rows"] for value in row["checks"].values())}
    (directory / "StateCycle.json").write_text(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
