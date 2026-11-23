# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from convert import open_document
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.Archive import ArchiveError
import convert.adapters.solidworks.Core.Native as native_reader


def roster():
    original = ROOT / "re/FeatureLadders2026"
    recovery = Path(__file__).resolve().parent
    manifest = json.loads((original / "Manifest.json").read_text())
    specifications = {row["case"]["id"]: row["case"] for row in manifest["cases"]}
    result = []
    for row in manifest["cases"]:
        if (
            row["case"]["application"] == "solidworks"
            and row["status"] == "native_completed"
        ):
            result.extend(
                (original, row["case"]["id"], item) for item in row["decodes"]
            )
    retained = json.loads((recovery / "Manifest.json").read_text())
    for row in retained["cases"]:
        result.extend((recovery, row["case"], item) for item in row["files"])
    assert len(result) == 144
    return result, specifications


def compare(raw, observed, specification, include_brep=True):
    document = open_document(
        raw, source_format="solidworks.sldprt", strict=True, include_brep=include_brep
    )
    (body,) = document.bodies
    assert body.topology.solid_count == 1
    bounds = body.topology.bounding_box
    assert bounds is not None
    lower = [getattr(bounds.minimum, axis) for axis in ("x", "y", "z")]
    upper = [getattr(bounds.maximum, axis) for axis in ("x", "y", "z")]
    centroid = [value * 1000 for value in observed["centroid_m"]]
    expected_low = [min(0, value * 2) for value in centroid]
    expected_high = [max(0, value * 2) for value in centroid]
    for actual, expected in zip(
        lower + upper, expected_low + expected_high, strict=True
    ):
        assert math.isclose(actual, expected, rel_tol=1e-8, abs_tol=1e-6), (
            actual,
            expected,
        )
    lengths = [high - low for low, high in zip(lower, upper, strict=True)]
    assert math.isclose(
        math.prod(lengths), observed["volume_m3"] * 1e9, rel_tol=1e-8, abs_tol=1e-6
    )
    area = 2 * sum(
        lengths[first] * lengths[second] for first, second in ((0, 1), (0, 2), (1, 2))
    )
    assert math.isclose(area, observed["area_m2"] * 1e6, rel_tol=1e-8, abs_tol=1e-6)
    assert all(
        math.isclose(a, b, abs_tol=1e-6)
        for a, b in zip(
            sorted(lengths), sorted(observed["parameters_mm"].values()), strict=True
        )
    )
    (sketch,) = document.sketches
    plane_id = {"front": 2, "top": 3, "right": 4}[specification["plane"]]
    assert sketch.support_plane_id == f"sldprt:plane:{plane_id}"
    assert sketch.attributes["support_plane_native_id"] == plane_id
    assert sketch.attributes["support_plane_source"] in {
        "plane-reference",
        "typed-archive-reference",
    }
    assert document.feature_timeline[-1].definition.reversed == specification["reverse"]
    return document


def check_sources():
    rows, specifications = roster()
    representatives = {}
    for package, identity, row in rows:
        path = package / row["native_path"]
        raw = path.read_bytes()
        truth = json.loads((path.parent / "GroundTruth.json").read_text())
        observed = next(item for item in truth["cases"] if item["case"] == path.stem)
        assert (
            hashlib.sha256(raw).hexdigest()
            == row["source_sha256"]
            == observed["sha256"]
        )
        specification = specifications[identity]
        compare(raw, observed, specification)
        compare(raw, observed, specification, include_brep=False)
        representatives.setdefault(
            (specification["plane"], specification["reverse"]),
            (raw, observed, specification),
        )
    assert len(representatives) == 6
    return len(rows), representatives


def reference(raw):
    archive = SldprtArchive.from_bytes(raw)
    stream = "Contents/Config-0-ResolvedFeatures"
    model = native_reader.decode_native_model(
        archive.streams["swXmlContents/KeyWords"], archive.streams[stream]
    )
    (sketch,) = model.sketches
    assert sketch.support_plane is not None
    return archive, stream, sketch.support_plane.offset


def change(raw, archive, stream, offset, delta, encoding, value):
    streams = archive.streams
    edited = bytearray(streams[stream])
    struct.pack_into(encoding, edited, offset + delta, value)
    streams[stream] = bytes(edited)
    return BuildSldprt(streams, Template=raw)


def check_variability(representatives):
    total = 0
    for raw, observed, specification in representatives.values():
        archive, stream, offset = reference(raw)
        for timestamp in (0, 1, 0x691A5AF6, 0xFFFFFFFF):
            edited = change(raw, archive, stream, offset, 4, "<I", timestamp)
            compare(edited, observed, specification)
            total += 1
    return total


def check_invalid(representatives):
    raw, _, _ = representatives[("top", False)]
    archive, stream, offset = reference(raw)
    edits = [
        (-87, "<H", 0),
        (-85, "<H", 0),
        (
            -85,
            "<H",
            struct.unpack_from("<H", archive.streams[stream], offset - 85)[0] + 1,
        ),
        (-83, "<H", 0),
        (
            -83,
            "<H",
            struct.unpack_from("<H", archive.streams[stream], offset - 83)[0] + 1,
        ),
        (-81, "<B", 1),
        (-56, "<I", 1),
        (-4, "<I", 18001),
        (0, "<i", 7),
        (8, "<H", 1),
        (10, "<i", 1),
        (14, "<B", 2),
        (15, "<d", float("nan")),
        (15, "<d", 0.5),
        (15, "<9d", (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)),
        (15, "<9d", (-1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, -1.0, 0.0)),
        (87, "<d", 0.001),
        (111, "<d", 2.0),
        (119, "<B", 1),
    ]
    for index, (delta, encoding, value) in enumerate(edits):
        if isinstance(value, tuple):
            edited_stream = bytearray(archive.streams[stream])
            struct.pack_into(encoding, edited_stream, offset + delta, *value)
            streams = archive.streams
            streams[stream] = bytes(edited_stream)
            edited = BuildSldprt(streams, Template=raw)
        else:
            edited = change(raw, archive, stream, offset, delta, encoding, value)
        for include_brep in (True, False):
            try:
                document = open_document(
                    edited,
                    source_format="solidworks.sldprt",
                    strict=True,
                    include_brep=include_brep,
                )
            except ArchiveError as error:
                assert index >= 9
                assert "invalid owned SOLIDWORKS principal sketch reference" in str(error)
            else:
                assert index < 9, "malformed principal pose produced a neutral document"
                (sketch,) = document.sketches
                assert sketch.attributes["support_plane_source"] == "stream-order"
    return {"rejections": len(edits) - 9, "unqualified_fallbacks": 9}


def check_rotated(representatives):
    raw, _, _ = representatives[("top", False)]
    archive, stream, offset = reference(raw)
    cosine = math.cos(math.radians(3))
    sine = math.sin(math.radians(3))
    basis = (cosine, -sine, 0, 0, 0, 1, -sine, -cosine, 0)
    assert cosine * cosine + sine * sine != 1.0
    streams = archive.streams
    edited = bytearray(streams[stream])
    struct.pack_into("<9d", edited, offset + 15, *basis)
    streams[stream] = bytes(edited)
    changed = BuildSldprt(streams, Template=raw)
    for include_brep in (True, False):
        document = open_document(
            changed, source_format="solidworks.sldprt", strict=True, include_brep=include_brep
        )
        (sketch,) = document.sketches
        assert sketch.support_plane_id == "sldprt:plane:3"
        assert sketch.attributes["support_plane_source"] == "plane-reference"
    return 2


def check_owner_scans():
    path = (
        ROOT
        / "re/solidworks/examples/Single Turbo Dual Overhead Cam V8 - KDP - 2024/BIELA.SLDPRT"
    )
    archive = SldprtArchive.open(path)
    original = native_reader.ReadPlaneOwner
    scans = 0

    def counted(*args):
        nonlocal scans
        scans += 1
        return original(*args)

    native_reader.ReadPlaneOwner = counted
    try:
        model = native_reader.decode_native_model(
            archive.streams["swXmlContents/KeyWords"],
            archive.streams["Contents/Config-0-ResolvedFeatures"],
        )
    finally:
        native_reader.ReadPlaneOwner = original
    assert len(model.sketches) > 1
    assert scans == 1, (scans, len(model.sketches))
    return scans


def check_custom():
    path = ROOT / "re/solidworks/examples/.SLDPRT/example.SLDPRT"
    archive = SldprtArchive.open(path)
    raw = archive.streams["Contents/Config-0-ResolvedFeatures"]
    model = native_reader.decode_native_model(
        archive.streams["swXmlContents/KeyWords"], raw
    )
    start = min(sketch.native_offset for sketch in model.sketches)
    assert native_reader.ReadPlaneOwner(raw, model.classes, start) is not None
    for include_brep in (True, False):
        document = open_document(path, strict=True, include_brep=include_brep)
        sketch = next(item for item in document.sketches if item.id == "sldprt:sketch:40")
        plane = next(item for item in document.support_planes if item.id == "sldprt:plane:39")
        assert plane.name == "Plane1"
        assert sketch.support_plane_id == plane.id
        assert sketch.attributes["support_plane_source"] == "stream-order"
    return 2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("choose an unused report path")
    count, representatives = check_sources()
    invalid = check_invalid(representatives)
    result = {
        "status": "passed",
        "native_files": count,
        "reader_comparisons": count * 2,
        "centroid_mismatches": 0,
        "timestamp_variants": check_variability(representatives),
        "invalid_reference_rejections": invalid["rejections"],
        "unqualified_reference_fallbacks": invalid["unqualified_fallbacks"],
        "rotated_frame_reads": check_rotated(representatives),
        "custom_plane_reads": check_custom(),
        "multi_sketch_owner_scans": check_owner_scans(),
        "bounds_evidence": "derived from origin-based native recipes and measured centroids",
        "mass_evidence": "cuboid properties derived from decoded bounds compared with native observations",
        "sdk_sources": {
            path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
            for path in (
                "src/convert/adapters/solidworks/Core/Native.py",
                "src/convert/adapters/solidworks/Core/Records/ReadPlanePose.py",
                "src/convert/adapters/solidworks/Core/Records/ReadPlaneOwner.py",
                "src/convert/adapters/solidworks/Core/Records/ReadLocalOwner.py",
            )
        },
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "fresh_native_acceptance": False,
        "full_semantics_verified": False,
        "native_conversion_acceptance": False,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
