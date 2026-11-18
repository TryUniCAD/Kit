import argparse
from hashlib import sha256
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("use a new disclosed regression publication path")
    raw = args.result.read_bytes()
    value = json.loads(raw)
    if not (value["passed"] and value["frozen_implementation_unchanged"] and value["local_worker_processes"] == 2
            and value["code_freeze_sha256"] == "47aa5d22d3a158653f8b3e8bff35c28a9e2dcd8b44286713028504e8217bfa1d"
            and not value["heldout_inputs_read"] and value["writer_output_count"] == value["native_processes_started"] == 0):
        raise ValueError("the exact unchanged disclosed regression is not qualified")
    cases = []
    for entry in value["cases"]:
        codec = entry["codec"]
        cases.append({"case": entry["case"], "parent_sha256": entry["file_sha256"], "child_sha256": entry["child_sha256"],
                      "stream_sha256": codec["stream_sha256"], "stream_bytes": codec["stream_bytes"],
                      "map_base": codec["map_base"], "map_terminal": codec["map_terminal"],
                      "byte_identity": codec["byte_identity"], "typed_readback_identity": codec["typed_readback_identity"],
                      "inherited_map_aliases": codec["inherited_map_aliases"], "inherited_objects_unchanged": codec["resolved_objects_unchanged"],
                      "codec_negative_count": len(codec["negatives"]),
                      "missing_schemas": codec["usage"]["read"]["missing_schemas"], "provisional_schemas": codec["usage"]["read"]["provisional_schemas"],
                      "native_byte_fields": codec["usage"]["read"]["native_byte_fields"],
                      "public": entry["public"], "typed_owners": entry["typed_owners"]})
    receipt = {key: value[key] for key in ("schema", "task_id", "scope", "passed", "code_freeze_sha256", "source_manifest_sha256",
                                          "baseline_D01_proof_sha256", "regression_tool_sha256", "native_source", "local_worker_processes",
                                          "frozen_implementation_unchanged", "native_processes_started", "writer_output_count", "heldout_inputs_read",
                                          "native_generated_perpendicular_acceptance", "full_family_coverage")}
    receipt.update({"raw_regression_sha256": sha256(raw).hexdigest(), "publisher_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
                    "cases": cases, "source_native_processes": 5,
                    "limitations": ["a second disclosed design with two saved states is additional source reader evidence rather than sealed qualification",
                                    "actual native endpoint order is compared independently from authored selection order",
                                    "no SDK source or frozen auditor changed for this regression",
                                    "no perpendicular generator or native generated acceptance"]})
    data = (json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    if any(text in data for text in (b"/Users/", b"\\\\Mac\\", b"C:\\", b"Z:\\")):
        raise ValueError("publication contains a machine path")
    args.output.write_bytes(data)
    print(json.dumps({"receipt_sha256": sha256(data).hexdigest(), "cases": len(cases), "frozen_implementation_unchanged": True}))


if __name__ == "__main__":
    main()
