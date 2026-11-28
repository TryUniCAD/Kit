import argparse
from hashlib import sha256
import json
from pathlib import Path
import platform

from convert import open_document, write_document
from convert.adapters import AdapterNotFoundError
from convert.adapters.Fusion.State.DecodeState import DecodeState
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from interchange import CadDocument


def digest(payload):
    return sha256(payload).hexdigest()


def check(source, folder):
    folder.mkdir()
    original = source.read_bytes()
    model = ReadDocument(original)
    row = {
        "source": str(source.resolve()),
        "source_sha256": digest(original),
        "source_bytes": len(original),
        "native_acceptance_measured": False,
        "semantic_edit_qualified": False,
    }
    stage = "strict_read"
    try:
        document = open_document(original, source_format="f3d")
        row["metadata_keys"] = sorted(document.metadata)
        row["parameter_names"] = [value.name for value in document.parameters]
        row["constraint_kinds"] = [
            relation.kind
            for sketch in document.sketches for relation in sketch.constraints
        ]
        stage = "persist_json"
        text = document.to_json()
        persisted = folder / "Document.json"
        persisted.write_text(text, encoding="utf-8", newline="\n")
        neutral = CadDocument.from_json(persisted.read_text(encoding="utf-8"))
        if neutral != document:
            raise ValueError("Persisted JSON changes the complete CadDocument")
        if DecodeState(neutral.metadata["fusion.native_state"]["model"]) != model:
            raise ValueError("Persisted JSON changes the complete typed DocumentModel")
        row["document_sha256"] = digest(persisted.read_bytes())
        row["persisted_document_equal"] = True
        stage = "public_write"
        if neutral.metadata.get("fusion.read_only") is not True:
            raise ValueError("Persisted saved Fusion document lost its read-only marker")
        target = folder / "Reemitted.f3d"
        try:
            write_document(neutral, target, destination_format="f3d", allow_carrier=False)
        except AdapterNotFoundError as error:
            if str(error) != "fusion.f3d does not support the destination":
                raise
            if target.exists():
                raise ValueError("Read-only write refusal left a destination") from error
            row.update(outcome="read_only_write_refused", error=str(error))
        else:
            raise ValueError("Read-only saved Fusion document unexpectedly exported")
    except (ValueError, TypeError, RuntimeError, AdapterNotFoundError) as error:
        row.update(outcome="unqualified", failed_stage=stage,
                   error_type=type(error).__name__, error=str(error))
    return row


def main():
    parser = argparse.ArgumentParser(description="Check unchanged saved Fusion public SDK/JSON boundaries without a CAD runtime")
    parser.add_argument("--source", type=Path, required=True, action="append")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    rows = [check(source, args.output / f"Case{index:02d}")
            for index, source in enumerate(args.source)]
    report = {"python": platform.python_version(), "cases": rows}
    (args.output / "Report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(report, indent=2))
    return 3 if all(row["outcome"] == "read_only_write_refused" for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
