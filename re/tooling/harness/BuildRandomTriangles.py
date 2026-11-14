from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

from convert import write_document as WriteDoc
from convert.adapters.solidworks.container.Container import SldprtArchive
from convert.adapters.solidworks.container.Format import (
    CONFIGURATION_STREAM,
    KEYWORDS_STREAM,
    RESOLVED_FEATURES_STREAM,
)
from convert.adapters.solidworks.core.Native import decode_native_model
from tests.convert.solidworks.resolved.SolidworksPolylineFiveTests import BuildDocument


def Analytic(points: tuple[tuple[float, float], ...], depth: float) -> dict[str, object]:
    area_twice = sum(
        points[index][0] * points[(index + 1) % 3][1]
        - points[(index + 1) % 3][0] * points[index][1]
        for index in range(3)
    )
    area = abs(area_twice) / 2.0
    perimeter = sum(
        math.hypot(
            points[(index + 1) % 3][0] - points[index][0],
            points[(index + 1) % 3][1] - points[index][1],
        )
        for index in range(3)
    )
    centre = (
        sum(point[0] for point in points) / 3.0,
        sum(point[1] for point in points) / 3.0,
        depth / 2.0,
    )
    return {
        "volume_mm3": area * depth,
        "area_mm2": 2.0 * area + perimeter * depth,
        "com_mm": centre,
    }


def Main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()
    arguments.output.mkdir(parents=True, exist_ok=True)
    rows = []
    for source_path in sorted(arguments.source.glob("tri3r*.SLDPRT")):
        archive = SldprtArchive.open(source_path)
        resolved_data = archive.require(RESOLVED_FEATURES_STREAM)
        model = decode_native_model(
            archive.require(KEYWORDS_STREAM),
            resolved_data,
            archive.require(CONFIGURATION_STREAM),
            resolved_stream=RESOLVED_FEATURES_STREAM,
        )
        profile = model.sketches[0].profiles[0]
        if profile.kind != "polyline" or len(profile.coordinates) != 6:
            raise ValueError(f"unsupported source profile {source_path}")
        points = tuple(
            (
                round(profile.coordinates[index], 6),
                round(profile.coordinates[index + 1], 6),
            )
            for index in range(0, 6, 2)
        )
        offset_shift = len(resolved_data) - 10601
        depth_values = tuple(
            struct.unpack_from("<d", resolved_data, offset + offset_shift)[0] * 1000.0
            for offset in (9408, 9480, 9968, 9992)
        )
        depth = round(depth_values[0], 6)
        if depth <= 0.0 or any(round(value, 6) != depth for value in depth_values):
            raise ValueError(f"source depth is inconsistent {source_path}: {depth_values}")
        target = arguments.output / f"{source_path.stem}-kit.SLDPRT"
        expected_metres = tuple(
            coordinate / 1000.0 for point in points for coordinate in point
        )
        if target.exists():
            existing = SldprtArchive.open(target).require(RESOLVED_FEATURES_STREAM)
            for offset, expected in zip(
                (6121, 6129, 6299, 6307, 6461, 6469), expected_metres, strict=True
            ):
                if existing[offset : offset + 8] != struct.pack("<d", expected):
                    raise ValueError(f"existing profile differs {target}")
            for offset in (9408, 9480, 9968, 9992):
                if existing[offset : offset + 8] != struct.pack("<d", depth / 1000.0):
                    raise ValueError(f"existing depth differs {target}")
            result = None
        else:
            result = WriteDoc(
                BuildDocument(points, Depth=depth), target, allow_carrier=False
            )
        generated = SldprtArchive.open(target).require(RESOLVED_FEATURES_STREAM)
        row = {
            "label": source_path.stem,
            "file": target.name,
            "points": points,
            "depth_mm": depth,
            **Analytic(points, depth),
            "resolved_sha256": hashlib.sha256(generated).hexdigest(),
            "vendor_loadable": None if result is None else result.IsVendorLoadable,
            "application_usable": None if result is None else result.IsAppUsable,
            "near_lossless": None if result is None else result.IsNearLossless,
        }
        rows.append(row)
        flags = (
            "reused"
            if result is None
            else f"{int(result.IsVendorLoadable)}{int(result.IsAppUsable)}{int(result.IsNearLossless)}"
        )
        print(
            f"GENERATED={row['label']} DEPTH={depth} "
            f"VOLUME={row['volume_mm3']:.12g} AREA={row['area_mm2']:.12g} "
            f"FLAGS={flags}"
        )
    if len(rows) != 64:
        raise ValueError(f"expected 64 sources, received {len(rows)}")
    (arguments.output / "manifest.json").write_text(
        json.dumps(rows, indent=2) + "\n", encoding="utf-8"
    )
    (arguments.output / "expectations.tsv").write_text(
        "".join(
            "\t".join(
                (
                    row["label"],
                    repr(row["depth_mm"]),
                    repr(row["volume_mm3"]),
                    repr(row["area_mm2"]),
                    *(repr(value) for value in row["com_mm"]),
                    row["file"],
                )
            )
            + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )
    print(f"CORPUS_GENERATED={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(Main())
