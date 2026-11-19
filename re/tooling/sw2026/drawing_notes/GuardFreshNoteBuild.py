import argparse
import codecs
from hashlib import sha256
import importlib
from json import dumps, loads
from pathlib import Path
import sys
from uuid import UUID

from BuildNoteArchive import build, note_input
from convert import open_document


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--guard-directory", required=True, type=Path)
    parser.add_argument("--intent", required=True, type=Path)
    parser.add_argument("--intent-sha256", required=True)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    raw = args.intent.read_bytes()
    if sha256(raw).hexdigest() != args.intent_sha256:
        raise ValueError("explicit note intent identity changed")
    record = loads(raw)
    sys.path.insert(0, str(args.guard_directory))
    from BlankRewriteGuard import OutputGuard

    for name in ("DocumentFeatureValidate", "DocumentReferenceValidate", "DocumentAssemblyValidate"):
        importlib.import_module("interchange.document.Validation." + name)
    importlib.import_module("interchange.document.Models.DocumentProvenance")
    for encoding in ("utf-8", "utf-16le", "utf-16be", "latin-1", "cp1252"):
        codecs.lookup(encoding)
    guard = OutputGuard(args.target.parent)
    sys.addaudithook(guard.event)
    guard.active = True
    try:
        inputs = note_input(
            record["initial_text"], record["initial_position"], record["sheet"], record["scale"],
            record["locator"], record["epoch"], UUID(record["block_id"]),
        )
        payload, streams, maps = build(inputs, origin_anchor=record["origin_anchor"], publish_identity=record.get("publish_identity", False))
        with args.target.open("xb") as target:
            if target.write(payload) != len(payload):
                raise OSError("short generated note write")
    finally:
        guard.active = False
    if guard.denied or guard.operations != ["output_write"]:
        raise ValueError("fresh note generation accessed undeclared data")
    sdk_visible = False
    if record["origin_anchor"]:
        opened = open_document(payload, source_format="solidworks.slddrw", strict=False)
        note, = opened.DrawingValue.Sheets[0].Notes or ()
        if note.TextValue != record["initial_text"] or [
            note.PositionValue.x, note.PositionValue.y, note.PositionValue.z,
        ] != record["initial_position"]:
            raise ValueError("generated partial SDK semantics changed")
        sdk_visible = True
    with args.report.open("x") as stream:
        stream.write(dumps({
            "schema": "kit.sw2026.fresh-note-host-worker.v1",
            "passed": True,
            "native_qualified": False,
            "runtime_input_reads": 0,
            "output_operations": guard.operations,
            "sdk_partial_note_visible": sdk_visible,
            "intent_sha256": args.intent_sha256,
            "container_sha256": sha256(payload).hexdigest(),
            "container_bytes": len(payload),
            "definition_length": len(streams["Contents/Definition"]),
            "logical_streams": {name: sha256(value).hexdigest() for name, value in streams.items()},
            "map_counter": maps.CounterValue,
            "theoretical_anchor": record["origin_anchor"],
            "name_and_display_identity_generated": record.get("publish_identity", False),
        }, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
