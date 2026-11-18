import argparse
import hashlib
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != args.source_sha256:
        raise ValueError("source identity changed")
    sys.path.insert(0, str(args.root / "src"))
    from convert import open_document
    from convert.adapters.solidworks.Archive.Construction.ThroughAll.ProjectThroughPart import (
        ProjectThroughPart,
    )
    from convert.adapters.solidworks.Core.Preparation.CheckPlainScope import (
        CheckPlainScope,
    )

    args.output.mkdir(parents=True, exist_ok=False)
    records = {}
    for label, options in [
        ("ordinary", {}),
        ("parametric", {"include_brep": False, "include_tessellation": False}),
    ]:
        try:
            document = open_document(args.source, **options)
            encoded = document.to_json(indent=2) + "\n"
            (args.output / (label + ".json")).write_text(encoded)
            item = {
                "document_sha256": hashlib.sha256(encoded.encode()).hexdigest(),
                "validation": list(document.validate()),
            }
            for title, fn in [
                ("plain_scope", CheckPlainScope),
                ("through_plan", ProjectThroughPart),
            ]:
                try:
                    value = fn(document)
                    item[title] = {"passed": True, "result_type": type(value).__name__}
                except Exception as err:
                    item[title] = {
                        "passed": False,
                        "error_type": type(err).__name__,
                        "error": str(err),
                    }
            records[label] = item
        except Exception as err:
            records[label] = {
                "read_passed": False,
                "error_type": type(err).__name__,
                "error": str(err),
            }
    report = {
        "source_sha256": args.source_sha256,
        "source_bytes": len(raw),
        "reads": records,
        "native_oracle_used": False,
        "native_acceptance": False,
    }
    (args.output / "ReadReceipt.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
