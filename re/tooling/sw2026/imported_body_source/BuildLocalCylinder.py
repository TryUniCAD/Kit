from argparse import ArgumentParser
from codecs import lookup
from collections import Counter
from dataclasses import asdict, dataclass, replace
from math import dist, isclose, isfinite, pi, sqrt, tau
from pathlib import Path
from struct import pack
from sys import float_info
import json

from BuildLocalBodyKernel import require_closed_unattributed
from LocalBodyEnvelope import (
    LocalBody,
    decode as decode_envelope,
    encode as encode_envelope,
)
from LocalBodyKernel import (
    BODY,
    EDGE,
    FACE,
    FIN,
    LOOP,
    REGION,
    SHELL,
    _render_local,
    fingerprint,
    require,
)
from VerifyBareImportPackage import guard_build
from convert.Geometry.Parasolid import (
    AnalyticGeom,
    BuildPartModel,
    NativeId,
    ParaStream,
    WritePointerMut,
)
from convert.Geometry.Revolve.SweepInput import CheckSweepFrame
from convert.Geometry.Revolve.SweepMetrics import MeasureFullTurn
from convert.Geometry.Revolve.SweepVector import DotVector
from convert.adapters.solidworks.Archive.Partition.KernelShapes import KKernelShapes
from convert.adapters.solidworks.Archive.Partition.LocalWrite.WriteXmtNodeMut import (
    WriteXmtNodeMut,
)
from convert.adapters.solidworks.Archive.Partition.ReadXmtNodeMut import ReadXmtNodeMut
from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtCursor import XmtCursor
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyFaces import (
    ReadBodyFaces,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.MakeLocalBodyTables import (
    MakeLocalTables,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalHead import (
    ReadLocalHead,
)
from interchange.Core.Common import FreezeMapping
from interchange.brep.Curves.BrepCurves import CircleCurve
from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface, PlaneSurface
from interchange.geometry.Models.VectorSpace import SpaceVector
from para.Partition import Node
from para.cylinder.CylinderTopology import cap_topology, translate
from para.rectangle.Allocate import DraftNode, Ref, index_fields
from para.rectangle.Geometry import chain, vector
from para.rectangle.RectanglePartition import complete_topology

CIRCLE, PLANE, CYLINDER = 31, 50, 51
INVENTORY = {
    BODY: 1,
    SHELL: 2,
    REGION: 2,
    FACE: 3,
    LOOP: 4,
    EDGE: 2,
    FIN: 4,
    CIRCLE: 2,
    PLANE: 2,
    CYLINDER: 1,
}
NODE_COUNT = sum(INVENTORY.values())
METRICS = ("volume_mm3", "area_mm2")
ROOT = Path(__file__).resolve().parents[4]
OWNING_SOURCES = (
    "re/tooling/sw2026/imported_body_source/LocalBodyEnvelope.py",
    "re/tooling/sw2026/imported_body_source/LocalBodyKernel.py",
    "re/tooling/sw2026/para/Partition.py",
    "re/tooling/sw2026/para/Schema.py",
    "re/tooling/sw2026/para/cylinder/CylinderTopology.py",
    "re/tooling/sw2026/para/rectangle/RectanglePartition.py",
    "src/convert/Geometry/Parasolid.py",
    "src/convert/Geometry/Revolve/SweepMetrics.py",
    "src/convert/adapters/solidworks/Archive/Partition/Fields/AnalyticShapes.py",
    "src/convert/adapters/solidworks/Archive/Partition/LocalWrite/WriteXmtNodeMut.py",
    "src/convert/adapters/solidworks/Archive/Partition/ReadXmtNodeMut.py",
    "src/convert/adapters/solidworks/Core/TypedResolved/Geometry/LocalBody/MakeLocalBodyTables.py",
    "tests/Convert/Solidworks/Research/ConstructionGuard.py",
)


@dataclass(frozen=True)
class CylinderInput:
    start_mm: tuple[float, float, float]
    axis: tuple[float, float, float]
    radial: tuple[float, float, float]
    radius_mm: float
    height_mm: float


CASES = {
    "TranslatedZ": CylinderInput(
        (16.25, -8.5, 3.375), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0), 6.75, 17.125
    ),
    "ReverseY": CylinderInput(
        (-11.125, 28.5, -4.875), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0), 4.625, 24.25
    ),
}


def negate(values):
    return tuple(-value for value in values)


def metres(values):
    return tuple(value / 1000.0 for value in values)


def finite_value(value):
    return type(value) in (int, float) and -float_info.max <= value <= float_info.max


def check_input(model):
    require(type(model) is CylinderInput, "cylinder requires the typed neutral input")
    require(
        all(
            finite_value(value) and value > 0.0
            for value in (model.radius_mm, model.height_mm)
        ),
        "radius and height must be positive and finite",
    )
    require(
        all(
            type(row) is tuple and len(row) == 3 and all(map(finite_value, row))
            for row in (model.start_mm, model.axis, model.radial)
        ),
        "cylinder vectors must be finite triples",
    )
    CheckSweepFrame(
        *(SpaceVector(*row) for row in (model.start_mm, model.axis, model.radial))
    )
    start = metres(model.start_mm)
    end = translate(start, model.axis, model.height_mm / 1000.0)
    require(
        all(map(isfinite, end))
        and start != end
        and translate(start, model.radial, model.radius_mm / 1000.0) != start
        and translate(end, model.radial, model.radius_mm / 1000.0) != end,
        "cylinder axial extent or radius is unrepresentable",
    )
    return start, end


def make_rim(body, cap, side_loop, point, cap_normal, cap_radial, radius):
    loop, edge, circle, plane, cap_fin, side_fin = cap_topology(
        cap, side_loop, body, point, cap_normal, cap_radial, radius, "-"
    )
    circle = replace(
        circle,
        fields={
            **circle.fields,
            "normal": negate(cap_normal),
            "x_axis": negate(cap_radial),
        },
    )
    return loop, edge, circle, plane, side_fin, cap_fin


def make_draft(model):
    start, end = check_input(model)
    axis, radial = (tuple(map(float, values)) for values in (model.axis, model.radial))
    radius = model.radius_mm / 1000.0
    body, void, solid, front_shell, back_shell = map(
        Ref, ("body", "void", "solid", "front-shell", "solid-shell")
    )
    far, near, side = map(Ref, ("far", "near", "side"))
    mantle = Ref("side:cylinder")
    side_loops = (Ref("side:far"), Ref("side:near"))
    face_order = (far, near, side)
    neighbors = chain(face.name for face in face_order)
    roots = (
        DraftNode(
            body,
            BODY,
            {
                "owner": 0,
                "shell": back_shell,
                "region": void,
                "edge": Ref("far:edge"),
                "vertex": 0,
                "boundary_point": 0,
                "boundary_curve": Ref("far:circle"),
                "boundary_surface": mantle,
                "attributes_features": 0,
                "attribute_chains": 0,
            },
        ),
        DraftNode(
            void,
            REGION,
            {
                "body": body,
                "next": solid,
                "previous": 0,
                "shell": front_shell,
                "type": "V",
            },
        ),
        DraftNode(
            solid,
            REGION,
            {
                "body": body,
                "next": 0,
                "previous": void,
                "shell": back_shell,
                "type": "S",
            },
        ),
        DraftNode(
            back_shell,
            SHELL,
            {"body": body, "region": solid, "face": far, "front_face": 0},
        ),
        DraftNode(
            front_shell,
            SHELL,
            {"body": 0, "region": void, "face": 0, "front_face": far},
        ),
    )
    faces = tuple(
        DraftNode(
            face,
            FACE,
            {
                "shell": back_shell,
                "front_shell": front_shell,
                "loop": loop,
                "surface": surface,
                "previous": previous,
                "next": following,
                "previous_front": previous,
                "next_front": following,
                "next_on_surface": 0,
                "previous_on_surface": 0,
                "sense": "+",
            },
        )
        for face, surface, loop in zip(
            face_order,
            (Ref("far:plane"), Ref("near:plane"), mantle),
            (Ref("far:loop"), Ref("near:loop"), side_loops[0]),
            strict=True,
        )
        for previous, following in (neighbors[face.name],)
    )
    loops = tuple(
        DraftNode(
            loop,
            LOOP,
            {"face": side, "halfedge": Ref(f"{loop.name}:fin"), "next": following},
        )
        for loop, following in zip(side_loops, (side_loops[1], 0), strict=True)
    )
    return (
        *roots,
        *faces,
        *loops,
        DraftNode(
            mantle,
            CYLINDER,
            {
                "owner": side,
                "sense": "+",
                "pvec": start,
                "axis": axis,
                "x_axis": radial,
                "radius": radius,
            },
        ),
        *make_rim(body, far, side_loops[0], end, axis, radial, radius),
        *make_rim(
            body, near, side_loops[1], start, negate(axis), negate(radial), radius
        ),
    )


def make_nodes(model):
    draft, next_id = complete_topology(make_draft(model))
    indices = {cell.ref: index for index, cell in enumerate(draft, 1)}
    require(len(indices) == NODE_COUNT, "cylinder wire identities must be distinct")
    result = []
    for cell in draft:
        fields = index_fields(cell.fields, indices)
        if cell.kind == BODY:
            fields["highest_node_id"] = next_id - 1
        result.append(Node(indices[cell.ref], cell.kind, fields))
    return tuple(result)


def read_typed(raw):
    header = ReadLocalHead(raw)
    require(header is not None, "unexpected local cylinder schema or role")
    cursor = XmtCursor(raw[header.body_offset :])
    nodes, offsets = {}, {}
    for index in range(1, NODE_COUNT + 1):
        offsets[index] = header.body_offset + cursor.OffsetValue
        kind = cursor.ReadKind()
        require(kind in INVENTORY, "unexpected local cylinder node kind")
        node = ReadXmtNodeMut(cursor, kind)
        require(node.IndexValue == index, "noncanonical local cylinder wire index")
        nodes[index] = node
    require(cursor.ReadKind() == 1, "local cylinder has extra records")
    cursor.FinishRead()
    return header, nodes, offsets


def write_typed(header, nodes):
    output = bytearray(pack(">HI", 239, 0))
    kinds = set()
    for node in nodes.values():
        WriteXmtNodeMut(output, node, KKernelShapes[node.KindValue], kinds)
    output.extend(pack(">H", 1))
    WritePointerMut(output, 0)
    return ParaStream(output, header.schema, header.description.encode("ascii"))


def node_fields(node, *names):
    return tuple(node.FieldsValue[name] for name in names)


def check_chain(head, nodes):
    indexes = tuple(node.IndexValue for node in nodes)
    require(
        head == indexes[0]
        and all(
            node_fields(node, "previous", "next") == (previous, following)
            for node, previous, following in zip(
                nodes, (0, *indexes[:-1]), (*indexes[1:], 0), strict=True
            )
        ),
        "local cylinder carrier chain differs",
    )


def check_ring(nodes, cap, side_loop, edge):
    cap_loop = RequireXmt(nodes, cap.Integer("loop"), LOOP)
    side_fin = RequireXmt(nodes, side_loop.Integer("halfedge"), FIN)
    cap_fin = RequireXmt(nodes, cap_loop.Integer("halfedge"), FIN)
    require(
        cap_loop.Integer("face") == cap.IndexValue
        and cap_loop.Integer("next") == 0
        and side_loop.IndexValue != cap_loop.IndexValue
        and edge.Integer("halfedge") == side_fin.IndexValue,
        "local cylinder rim owner differs",
    )
    for fin, opposite, loop, sense in (
        (side_fin, cap_fin, side_loop, "+"),
        (cap_fin, side_fin, cap_loop, "-"),
    ):
        require(
            node_fields(
                fin,
                "forward",
                "backward",
                "other",
                "loop",
                "edge",
                "vertex",
                "next_at_vx",
                "curve",
                "sense",
            )
            == (
                fin.IndexValue,
                fin.IndexValue,
                opposite.IndexValue,
                loop.IndexValue,
                edge.IndexValue,
                0,
                0,
                0,
                sense,
            ),
            "local cylinder requires one self-linked vertex-free fin per rim use",
        )
    circle = RequireXmt(nodes, edge.Integer("curve"), CIRCLE)
    cap_plane = RequireXmt(nodes, cap.Integer("surface"), PLANE)
    require(
        circle.Integer("owner") == edge.IndexValue
        and cap_plane.Integer("owner") == cap.IndexValue
        and circle.String("sense")
        == cap_plane.String("sense")
        == cap.String("sense")
        == "+"
        and node_fields(circle, "centre", "normal", "x_axis")
        == (
            ReadXmtVector(cap_plane, "pvec"),
            negate(ReadXmtVector(cap_plane, "normal")),
            negate(ReadXmtVector(cap_plane, "x_axis")),
        ),
        "local cylinder cap and circular rim have different orientation or support",
    )
    return cap_loop, cap_plane, circle


def verify_graph(nodes):
    require(
        Counter(node.KindValue for node in nodes.values()) == INVENTORY,
        "local cylinder has a different resident topology",
    )
    require_closed_unattributed(
        tuple(
            Node(node.IndexValue, node.KindValue, dict(node.FieldsValue))
            for node in nodes.values()
        )
    )
    body = nodes[1]
    persistent = tuple(
        node.Integer("node_id")
        for node in nodes.values()
        if node.KindValue not in (BODY, FIN)
    )
    require(
        set(persistent) == set(range(1, body.Integer("highest_node_id") + 1))
        and len(persistent) == len(set(persistent))
        and node_fields(
            body, "vertex", "boundary_point", "owner", "previous", "next", "child"
        )
        == (0,) * 6,
        "local cylinder root or persistent identities differ",
    )
    far, near, side = (nodes[index] for index in ReadBodyFaces(nodes, body, 3))
    mantle = RequireXmt(nodes, side.Integer("surface"), CYLINDER)
    require(
        mantle.Integer("owner") == side.IndexValue
        and side.String("sense") == mantle.String("sense") == "+",
        "local cylinder mantle has a foreign owner or reversed sense",
    )
    side_far = RequireXmt(nodes, side.Integer("loop"), LOOP)
    side_near = RequireXmt(nodes, side_far.Integer("next"), LOOP)
    require(
        side_far.IndexValue != side_near.IndexValue
        and side_near.Integer("next") == 0
        and side_far.Integer("face") == side_near.Integer("face") == side.IndexValue,
        "local cylinder mantle requires exactly two rings",
    )
    edges = tuple(
        nodes[index]
        for index in WalkXmtChain(
            nodes,
            body.Integer("edge"),
            EDGE,
            OwnerField="owner",
            OwnerValue=body.IndexValue,
        )
    )
    require(len(edges) == 2, "local cylinder must own exactly two boundary edges")
    far_loop, far_plane, far_circle = check_ring(nodes, far, side_far, edges[0])
    near_loop, near_plane, near_circle = check_ring(nodes, near, side_near, edges[1])
    require(
        len({loop.IndexValue for loop in (far_loop, near_loop, side_far, side_near)})
        == 4,
        "local cylinder reuses a boundary loop",
    )
    check_chain(body.Integer("boundary_curve"), (far_circle, near_circle))
    check_chain(body.Integer("boundary_surface"), (mantle, far_plane, near_plane))
    axis, radial = node_fields(mantle, "axis", "x_axis")
    start, end = (ReadXmtVector(plane, "pvec") for plane in (near_plane, far_plane))
    CheckSweepFrame(*(SpaceVector(*row) for row in (start, axis, radial)))
    height = dist(start, end)
    require(
        height > 0.0
        and dist(translate(start, axis, height), end) <= 1e-14 * height
        and ReadXmtVector(mantle, "pvec") == start
        and node_fields(far_plane, "normal", "x_axis") == (axis, radial)
        and node_fields(near_plane, "normal", "x_axis")
        == (negate(axis), negate(radial))
        and mantle.FieldsValue["radius"]
        == far_circle.FieldsValue["radius"]
        == near_circle.FieldsValue["radius"]
        and isfinite(mantle.FieldsValue["radius"])
        and mantle.FieldsValue["radius"] > 0.0,
        "local cylinder has inconsistent radius, frame, or signed cap extent",
    )


def make_neutral(nodes, offsets):
    tables = MakeLocalTables(nodes, offsets)
    field_order = {
        CIRCLE: ("centre", "normal", "x_axis", "radius"),
        CYLINDER: ("pvec", "axis", "radius", "x_axis"),
    }
    for index, node in nodes.items():
        fields = field_order.get(node.KindValue)
        if fields is None:
            continue
        values = tuple(
            component
            for value in node_fields(node, *fields)
            for component in (value if type(value) is tuple else (value,))
        )
        carrier_role = "curve" if node.KindValue == CIRCLE else "surface"
        carrier = AnalyticGeom(
            node.KindValue, NativeId(carrier_role, index + 1), values
        )
        require(
            isinstance(carrier, (CircleCurve, CylinderSurface)),
            "unsupported local cylinder carrier",
        )
        attributes = FreezeMapping(
            {
                "sense": node.String("sense") == "+",
                "header_references": tuple(
                    node.Integer(key) + 1
                    for key in ("attributes_features", "owner", "previous", "next")
                ),
            }
        )
        target = tables.curves if carrier_role == "curve" else tables.surfaces
        target[index + 1] = replace(carrier, attributes=attributes)
    return BuildPartModel(tables)


def measure_neutral(model):
    (side,) = (
        surface for surface in model.surfaces if type(surface) is CylinderSurface
    )
    caps = tuple(surface for surface in model.surfaces if type(surface) is PlaneSurface)
    counts = {
        name: len(getattr(model, name))
        for name in (
            "bodies",
            "regions",
            "shells",
            "faces",
            "loops",
            "edges",
            "coedges",
            "vertices",
            "curves",
            "surfaces",
        )
    }
    require(
        tuple(counts.values()) == (1, 1, 1, 3, 4, 2, 4, 2, 2, 3)
        and len(caps) == 2
        and all(type(curve) is CircleCurve for curve in model.curves)
        and model.regions[0].solid
        and model.shells[0].closed
        and all(
            edge.start_vertex_id == edge.end_vertex_id
            and (edge.start_parameter, edge.end_parameter) == (0.0, tau)
            and not edge.degenerate
            for edge in model.edges
        )
        and all(
            sorted(
                coedge.reversed for coedge in model.coedges if coedge.edge_id == edge.id
            )
            == [False, True]
            for edge in model.edges
        )
        and all(face.same_sense for face in model.faces)
        and sorted(len(face.loop_ids) for face in model.faces) == [1, 1, 2]
        and not model.validate(),
        "typed cylinder did not restore one complete neutral periodic solid",
    )
    near, far = sorted(caps, key=lambda plane: DotVector(plane.origin, side.axis))
    start, end = vector(near.origin), vector(far.origin)
    height, radius = dist(start, end), side.radius
    require(
        start == vector(side.origin)
        and vector(near.normal) == negate(vector(side.axis))
        and vector(far.normal) == vector(side.axis)
        and {vector(curve.center) for curve in model.curves} == {start, end}
        and all(curve.radius == radius for curve in model.curves),
        "typed cylinder neutral carriers changed support, orientation or radii",
    )
    meridian = ((0.0, 0.0), (radius, 0.0), (radius, height), (0.0, height))
    volume, area, bounds = MeasureFullTurn(
        meridian, near.origin, side.axis, side.reference_direction
    )
    return counts, {
        "volume_mm3": volume,
        "area_mm2": area,
        "centroid_mm": tuple((a + b) / 2.0 for a, b in zip(start, end, strict=True)),
        "bounds_mm": (vector(bounds.minimum), vector(bounds.maximum)),
    }


def expected_measures(model):
    start, axis, height, radius = (
        model.start_mm,
        model.axis,
        model.height_mm,
        model.radius_mm,
    )
    end = translate(start, axis, height)
    spread = tuple(radius * sqrt(max(0.0, 1.0 - value * value)) for value in axis)
    coordinates = tuple(zip(start, end, spread, strict=True))
    return {
        "volume_mm3": pi * radius**2 * height,
        "area_mm2": 2.0 * pi * radius * (radius + height),
        "centroid_mm": translate(start, axis, height / 2.0),
        "bounds_mm": (
            tuple(min(a, b) - radial for a, b, radial in coordinates),
            tuple(max(a, b) + radial for a, b, radial in coordinates),
        ),
    }


def measure_case(name, model):
    draft = make_nodes(model)
    raw = _render_local(draft)
    header, nodes, offsets = read_typed(raw)
    require(
        draft
        == tuple(
            Node(node.IndexValue, node.KindValue, dict(node.FieldsValue))
            for node in nodes.values()
        )
        and write_typed(header, nodes) == raw,
        "independent typed cylinder replay changed bytes",
    )
    verify_graph(nodes)
    envelope = LocalBody(name, raw)
    framed = encode_envelope(envelope)
    require(
        decode_envelope(framed) == envelope,
        "generated cylinder diverged in the local envelope",
    )
    counts, observed = measure_neutral(make_neutral(nodes, offsets))
    expected = expected_measures(model)
    expected_vectors = (expected["centroid_mm"], *expected["bounds_mm"])
    observed_vectors = (observed["centroid_mm"], *observed["bounds_mm"])
    require(
        all(isclose(observed[name], expected[name], rel_tol=2e-12) for name in METRICS)
        and all(
            dist(actual, target) <= 2e-10
            for actual, target in zip(observed_vectors, expected_vectors, strict=True)
        ),
        "decoded cylinder geometry differs from independent analytic expectation",
    )
    return raw, {
        "input": asdict(model),
        "raw": fingerprint(raw),
        "local_envelope": fingerprint(framed),
        "resident": {
            KKernelShapes[kind].NameValue: count
            for kind, count in sorted(INVENTORY.items())
        },
        "neutral_counts": counts,
        "expected": expected,
        "decoded": observed,
        "body_index": 1,
        "attribute_count": 0,
        "outside_references": 0,
        "typed_replay_exact": True,
        "local_envelope_exact": True,
    }


def refusal(operation, value, reason):
    try:
        operation(value)
    except ValueError as error:
        require(reason in str(error), f"wrong refusal: {error}")
        return str(error)
    raise ValueError(f"expected refusal for {reason}")


def malformed_cases(raw):
    model = CASES["TranslatedZ"]
    _, nodes, _ = read_typed(raw)
    fin = next(node for node in nodes.values() if node.KindValue == FIN)
    circles = [node for node in nodes.values() if node.KindValue == CIRCLE]
    far, near = circles
    altered_fin = replace(
        fin, FieldsValue={**fin.FieldsValue, "vertex": far.IndexValue}
    )
    wrong_basis = replace(
        near,
        FieldsValue={
            **near.FieldsValue,
            "x_axis": negate(ReadXmtVector(near, "x_axis")),
        },
    )
    radius_mismatch = replace(
        far, FieldsValue={**far.FieldsValue, "radius": far.FieldsValue["radius"] * 1.25}
    )
    return {
        "zero_radius": refusal(
            make_nodes, replace(model, radius_mm=0.0), "positive and finite"
        ),
        "infinite_height": refusal(
            make_nodes, replace(model, height_mm=float("inf")), "positive and finite"
        ),
        "nonorthogonal_frame": refusal(
            make_nodes, replace(model, radial=model.axis), "orthonormal"
        ),
        "unrepresentable_extent": refusal(
            make_nodes, replace(model, start_mm=(0.0, 0.0, 1e30)), "unrepresentable"
        ),
        "trailing_bytes": refusal(read_typed, raw + b"x", "terminator differs"),
        "foreign_vertex": refusal(
            verify_graph, nodes | {fin.IndexValue: altered_fin}, "vertex-free fin"
        ),
        "cap_rim_basis_disagreement": refusal(
            verify_graph,
            nodes | {near.IndexValue: wrong_basis},
            "orientation or support",
        ),
        "radius_disagreement": refusal(
            verify_graph,
            nodes | {far.IndexValue: radius_mismatch},
            "inconsistent radius",
        ),
    }


def main():
    parser = ArgumentParser(
        description="Build and verify two model-only bare Parasolid cylinders"
    )
    parser.add_argument(
        "--artifacts",
        type=Path,
        help="new directory outside the Kit checkout for the two binary exchanges",
    )
    args = parser.parse_args()
    destination = args.artifacts.resolve() if args.artifacts is not None else None
    if destination is not None:
        require(
            not destination.is_relative_to(ROOT) and not destination.exists(),
            "artifact destination must be unused and outside Kit",
        )
    for codec in ("ascii", "latin-1", "utf-8", "utf-16-le"):
        lookup(codec)
    with guard_build():
        cases = {name: measure_case(name, model) for name, model in CASES.items()}
        require(
            len({row["raw"]["sha256"] for _, row in cases.values()}) == len(cases),
            "changing neutral inputs must change the local cylinder payload",
        )
        refusals = malformed_cases(cases["TranslatedZ"][0])
    if destination is not None:
        destination.mkdir()
        for name, (raw, _) in cases.items():
            with (destination / f"{name}.x_b").open("xb") as handle:
                handle.write(raw)
    print(
        json.dumps(
            {
                "schema": "kit.sw2026.generated-local-cylinder-preflight.v1",
                "observer": fingerprint(Path(__file__).read_bytes()),
                "owning_sources_sha256": {
                    path: fingerprint((ROOT / path).read_bytes())["sha256"]
                    for path in OWNING_SOURCES
                },
                "construction_runtime_reads": 0,
                "native_loadability": "pending",
                "native_writer_outputs": 0,
                "heldout_cases": 0,
                "cases": {name: report for name, (_, report) in cases.items()},
                "refusals": refusals,
            },
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
