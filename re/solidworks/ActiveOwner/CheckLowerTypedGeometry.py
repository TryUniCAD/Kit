from argparse import ArgumentParser
from hashlib import sha256
import json
from math import fsum, hypot
from pathlib import Path
from types import MappingProxyType

from convert.Geometry.Parasolid import BuildPartModel
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.Partition.PartMass import PlanarMoments
from convert.adapters.solidworks.Core.Partition.PartMassRings import ReadMassRings
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.MakeLocalBodyTables import (
    MakeLocalTables,
)
from interchange.geometry.Models.VectorSpace import SpaceVector


def digest(raw):
    return sha256(raw).hexdigest()


def stored(value):
    if isinstance(value, list):
        return tuple(stored(item) for item in value)
    if isinstance(value, dict) and set(value) == {"$bytes_hex"}:
        return bytes.fromhex(value["$bytes_hex"])
    return value


def coordinates(vector):
    return vector.x, vector.y, vector.z


def ring_normal(ring):
    next_points = (*ring[1:], ring[0])
    return tuple(
        fsum(
            coordinates(a)[i] * coordinates(b)[j]
            - coordinates(a)[j] * coordinates(b)[i]
            for a, b in zip(ring, next_points, strict=True)
        )
        for i, j in ((1, 2), (2, 0), (0, 1))
    )


def compare(model, native):
    body = native["initial"]["state"]["body"]["body_geometry"]
    expected_edges = {
        tuple(sorted((tuple(edge["start_mm"]), tuple(edge["end_mm"]))))
        for edge in body["edges"]
    }
    vertices = {row.id: coordinates(row.point) for row in model.vertices}
    pairs = {
        tuple(sorted((vertices[edge.start_vertex_id], vertices[edge.end_vertex_id])))
        for edge in model.edges
    }
    rings = ReadMassRings(model)
    signed, mx, my, mz = PlanarMoments(model, SpaceVector(0, 0, 0))
    centroid = (mx / signed, my / signed, mz / signed)
    normals = tuple(ring_normal(ring) for ring in rings)
    dots = [
        fsum(
            n * (p - center)
            for n, p, center in zip(normal, coordinates(ring[0]), centroid, strict=True)
        )
        for normal, ring in zip(normals, rings, strict=True)
    ]
    area = fsum(hypot(*normal) / 2 for normal in normals)
    counts = tuple(
        len(getattr(model, field))
        for field in ("bodies", "faces", "edges", "vertices", "loops", "coedges")
    )
    assert counts == (1, 6, 12, 8, 6, 24)
    assert model.shells[0].closed and len(model.shells) == 1
    assert model.regions[0].solid and len(model.regions) == 1
    assert pairs == expected_edges and len(pairs) == 12
    assert len(dots) == 6 and all(dot > 0 for dot in dots)
    assert signed == 9600.0 and area == 3040.0 and centroid == (20.0, 10.0, 6.0)
    return {
        "body_face_edge_vertex_loop_fin_counts": counts,
        "closed": True,
        "exact_native_unordered_edges": len(pairs),
        "signed_volume_mm3": signed,
        "surface_area_mm2": area,
        "centroid_mm": centroid,
        "outward_ring_dots": dots,
    }


def main(walk_path, native_path, output):
    if not __debug__:
        raise RuntimeError(
            "run without Python optimization to preserve evidence checks"
        )
    walk_raw = walk_path.read_bytes()
    native_raw = native_path.read_bytes()
    assert (
        digest(walk_raw)
        == "3519ddfafa1ef3cebb86f479719acb944ca36d5eb97438f384b6c1d29c75b967"
    )
    assert (
        digest(native_raw)
        == "800b853bde09fd171487262ab0d1f49e73a621c500435895c281908bdc0153d0"
    )
    walk = json.loads(walk_raw)
    assert walk["physical_complete"] and walk["all_declared_pointer_targets_exist"]
    nodes = {
        row["index"]: XmtNode(
            row["index"],
            row["kind"],
            MappingProxyType(
                {name: stored(value) for name, value in row["fields"].items()}
            ),
        )
        for row in walk["records"]
    }
    spans = {row["index"]: row["body_span"][0] for row in walk["records"]}
    tables = MakeLocalTables(nodes, spans)
    model = BuildPartModel(tables)
    issues = model.validate()
    assert not issues, issues
    result = compare(model, json.loads(native_raw))
    assert walk_path.read_bytes() == walk_raw and native_path.read_bytes() == native_raw
    receipt = {
        "schema": "kit.research.p03-lower-typed-geometry.v1",
        "walk_sha256": digest(walk_raw),
        "native_record_sha256": digest(native_raw),
        "method_sha256": digest(Path(__file__).read_bytes()),
        "result": result,
        "source_annotation_bindings": False,
        "native_launches": 0,
        "public_decoder_calls": 0,
        "sdk_schema_mutation": False,
    }
    with output.open("x", encoding="utf-8", newline="\n") as target:
        json.dump(receipt, target, indent=2, sort_keys=True)
        target.write("\n")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--walk", type=Path, required=True)
    parser.add_argument("--native-record", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    main(args.walk, args.native_record, args.output)
