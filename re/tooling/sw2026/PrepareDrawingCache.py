from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(Path(__file__).with_name("serial"))]

from CheckDrawingDefinitions import SOURCE_LOCK, checked_artifacts, digest, require
from DrawingCacheCases import CASES, CONTROL, SCHEMA, TOOL_NAMES, input_file
from convert.adapters.solidworks.Container.Container import EmitSldprt, SldprtArchive, TemplateFields


def prepare(*, corpus, output):
    output = output.resolve()
    require(not output.is_relative_to(ROOT), "drawing diagnostic output must be outside the checkout")
    lock_bytes = SOURCE_LOCK.read_bytes()
    lock = json.loads(lock_bytes)
    control = next(case for case in lock["cases"] if case["name"] == CONTROL and case["split"] == "discovery")
    native, authored, _ = checked_artifacts(corpus, control)
    require(authored["view"] is None, "the disclosed control must be an empty drawing")
    archive = SldprtArchive.from_bytes(native)
    require(archive.format_version == 4, "unsupported drawing control container")
    signatures, type_ids = TemplateFields(native, archive)
    streams = archive.streams
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    rows = []
    for name, omitted in CASES:
        path = input_file(output, name)
        path.parent.mkdir(parents=True, exist_ok=False)
        if omitted is not None:
            require(omitted in streams, f"drawing diagnostic source lacks {omitted}")
        subset = {key: data for key, data in streams.items() if key != omitted}
        variant = native if name == "Pristine" else EmitSldprt(
            list(subset.items()), archive.file_id, archive.format_version, signatures, type_ids
        )
        check = SldprtArchive.from_bytes(variant)
        require(
            check.file_id == archive.file_id and check.format_version == archive.format_version and check.streams == subset,
            f"repacking changed a retained drawing stream in {name}",
        )
        path.write_bytes(variant)
        rows.append({
            "name": name, "omitted": omitted, "sha256": digest(variant),
            "bytes": len(variant), "retained_stream_count": len(subset),
        })
    require(rows[0]["sha256"] == control["native_sha256"], "private unmodified drawing differs from the locked source")
    rechecked, _, _ = checked_artifacts(corpus, control)
    require(rechecked == native, "original disclosed drawing changed during diagnostic staging")
    packet = {
        "schema": SCHEMA, "source_lock_sha256": digest(lock_bytes), "control_sha256": digest(native),
        "oracle_sha256": lock["oracle_sha256"], "expected": authored, "cases": rows,
        "tool_hashes": {name: digest(Path(__file__).with_name(name).read_bytes()) for name in TOOL_NAMES},
        "writer_output_count": 0, "native_acceptance": False,
    }
    manifest = output / "Trial.json"
    manifest.write_text(json.dumps(packet, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return manifest, len(rows)


def main():
    parser = argparse.ArgumentParser(description="Stage an immutable blank drawing and independent cache omissions outside the checkout")
    parser.add_argument("corpus", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    manifest, cases = prepare(corpus=args.corpus, output=args.output)
    print(json.dumps({"manifest": str(manifest), "manifest_sha256": digest(manifest.read_bytes()), "cases": cases}))


if __name__ == "__main__":
    main()
