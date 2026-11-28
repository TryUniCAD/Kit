from argparse import ArgumentParser
from hashlib import sha256
from json import dumps, loads
from pathlib import Path
from struct import unpack_from


PHASES = {
    "ControlBefore": "pristine",
    "NativeSource": "reference",
    "Generated": "candidate",
    "ControlAfter": "pristine",
}
FRAMES = ("Initial", "Edited", "EditedRebuilt", "Inserted", "InsertedRebuilt")


def pixels(path, frame):
    raw = path.read_bytes()
    if raw[:2] != b"BM" or sha256(raw).hexdigest() != frame["sha256"]:
        raise ValueError("unexpected bitmap identity")
    offset = unpack_from("<I", raw, 10)[0]
    width, height, planes, bpp, compression = unpack_from("<iiHHI", raw, 18)
    if (width, abs(height)) != (frame["width"], frame["height"]) or width <= 0 or not height:
        raise ValueError("unexpected viewport shape")
    if planes != 1 or compression or bpp not in (24, 32):
        raise ValueError("expected ordinary 24- or 32-bit RGB rows")
    size = bpp // 8
    stride = (width * size + 3) & ~3
    if offset + stride * abs(height) > len(raw) or sha256(raw[offset:]).hexdigest() != frame["pixel_sha256"]:
        raise ValueError("unexpected bitmap pixel storage")
    rows = [raw[offset + y * stride:offset + y * stride + width * size] for y in range(abs(height))]
    return (width, abs(height), size), rows if height < 0 else rows[::-1]


def delta(a, b):
    shape, before = a
    after_shape, after = b
    if shape != after_shape:
        raise ValueError("viewport shapes differ")
    width, height, size = shape
    points = [(x, y) for y in range(height) if before[y] != after[y] for x in range(width)
              if before[y][x * size:x * size + 3] != after[y][x * size:x * size + 3]]
    if not points:
        return {"changed_pixels": 0, "bounds_xyxy": None}
    x, y = zip(*points, strict=True)
    return {"changed_pixels": len(points), "bounds_xyxy": [min(x), min(y), max(x), max(y)]}


def main():
    parser = ArgumentParser()
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--sha256", required=True)
    result = parser.parse_args()
    raw = result.receipt.read_bytes()
    digest = sha256(raw).hexdigest()
    source = loads(raw)
    if digest != result.sha256 or source["schema"] != "kit.sw2026.disclosed-drawing-memory-changes.v1":
        raise ValueError("unexpected native diagnostic receipt")
    if not (source["complete"] and source["healthy_controls"] and source["distinct_processes"] == 4
            and source["phases"].keys() == PHASES.keys()):
        raise ValueError("native diagnostic was incomplete")
    observations = {}
    captures = {}
    for role, kind in PHASES.items():
        row = source["phases"][role]
        if not (row["passed"] and row["immutable_input"] and row["open"] == [0, 0]):
            raise ValueError("native phase was not clean")
        frame_names = [name for name in FRAMES if kind != "pristine" or not name.startswith("Edited")]
        frame_keys = [name.replace("Rebuilt", "_rebuilt").lower() + "_bitmap" for name in frame_names]
        capture = {name: row[key] for name, key in zip(frame_names, frame_keys, strict=True)}
        frames = {name: pixels(result.receipt.parent / role / (name + ".bmp"), v) for name, v in capture.items()}
        captures[role] = frames
        anchor = "Initial" if kind == "pristine" else "EditedRebuilt"
        changes = {
            "insert_on_redraw": delta(frames[anchor], frames["Inserted"]),
            "insert_after_rebuild": delta(frames[anchor], frames["InsertedRebuilt"]),
        }
        if kind != "pristine":
            changes.update(edit_on_redraw=delta(frames["Initial"], frames["Edited"]),
                           edit_after_rebuild=delta(frames["Initial"], frames["EditedRebuilt"]))
        observations[role] = {
            "kind": kind, "native_open": row["open"], "input_sha256": row["input_sha256"],
            "bitmap_hashes": {name: frame["sha256"] for name, frame in capture.items()},
            "pixel_changes": changes, "initial_note_count": row["initial"]["annotation_count"],
            "final_note_count": len(row["inserted_annotations"]),
            "display_toggles": row["preferences"]["toggles"],
        }
    baseline = captures["ControlBefore"]["Initial"]
    print(dumps({
        "schema": "kit.sw2026.disclosed-drawing-memory-bitmap-deltas.v1",
        "native_result_sha256": digest, "oracle_build": source["phases"]["Generated"]["identity"]["file_version"],
        "basis_job_sha256": source["job_sha256"], "heldout_source_reads": source["heldout_source_reads"],
        "native_saves": source["document_saves"], "distinct_processes": source["distinct_processes"],
        "settings_writes": source["settings_writes"], "healthy_controls": source["healthy_controls"],
        "generated_initial_vs_pristine": delta(baseline, captures["Generated"]["Initial"]),
        "native_initial_vs_pristine": delta(baseline, captures["NativeSource"]["Initial"]),
        "phases": observations,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
