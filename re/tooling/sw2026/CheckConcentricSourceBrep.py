from dataclasses import dataclass
from hashlib import sha256
from math import dist, fsum, isclose, tau
from types import MappingProxyType

from convert.Geometry.Parasolid import NativeId
from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Assembly.Assembly import DecodeNativeAsm
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, ReadRows, RequireNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.AssemblyPreparation.Placements.ReadAsmPlace import ReadAsmPlace
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CheckCylSide import CheckCylSide
from convert.adapters.solidworks.Core.TypedMates.Cylinders.MakeCylContext import MakeCylContext
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylEnd import ReadCylEnd
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylWords import ReadCylWords
from convert.adapters.solidworks.Core.TypedMates.PublicMateEnv import PublicMateEnv
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.CheckBrepOwners import CheckBrepOwners
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadCylBodyTree import ReadCylBodyTree
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.brep.Curves.BrepCurves import CircleCurve
from interchange.brep.Surfaces.BrepSurfaces import CylinderSurface, PlaneSurface
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.Transform import Transform


def require(value, why):
    if not value:
        raise ValueError("saved cylinder correspondence: " + why)


def vector(value):
    return (value.x, value.y, value.z)


def dot(a, b):
    return fsum(x * y for x, y in zip(a, b, strict=True))


def shift(point, vector, amount):
    return tuple(p + amount * v for p, v in zip(point, vector, strict=True))


def same_point(left, right):
    return dist(left, right) <= 1e-9


def same_axis(left, right):
    return dist(left, right) <= 1e-10


def same_value(left, right):
    return isclose(left, right, rel_tol=1e-12, abs_tol=1e-9)


def wire_index(public_id):
    return int(public_id.rsplit(":", 1)[1]) - 1


def kernel_point(native, key):
    return tuple(1000 * value for value in ReadXmtVector(native, key))


def bind_public_inventory(model, tree):
    for name, kind, identifiers in (
        ("faces", "face", tree.FaceIds), ("surfaces", "surface", tree.SurfaceIds),
        ("loops", "loop", tree.LoopIds), ("coedges", "coedge", tree.FinIds),
        ("edges", "edge", tree.EdgeIds), ("curves", "curve", tree.CurveIds),
    ):
        rows = getattr(model, name)
        require(len(rows) == len(identifiers)
                and {row.id for row in rows} == {NativeId(kind, index + 1) for index in identifiers},
                "public " + name + " differ from the actual selected body inventory")


@dataclass(frozen=True)
class Rim:
    cap_face: str
    cap_loop: str
    cap_coedge: str
    side_loop: str
    side_coedge: str
    edge: str
    curve: str
    seam: str
    selector: int


@dataclass(frozen=True)
class CylinderRoles:
    child: object
    native: object
    producer: str
    side_face: str
    radius: float
    centers: tuple
    design_axis: tuple
    reference_direction: tuple
    carrier_origin: tuple
    carrier_sign: int
    rims: object


def read_design_cylinder(document, native):
    model = document.brep
    if model is None:
        raise ValueError("saved cylinder correspondence: selected child needs its actual public B-rep")
    feature_id = NativeNodeId(native.FeatureValue)
    proof = document.metadata.get("solidworks.native_body_names", {})
    require(document.source.sha256 == native.SourceHash and str(document.units) == "mm"
            and len(document.configurations) == len(document.bodies) == len(model.bodies) == 1
            and proof.get("complete_brep_binding") is True and proof.get("name_owner") == "implicit_kernel"
            and proof.get("atom_manager_id") == native.AtomValue
            and proof.get("last_modifying_feature_id") == feature_id
            and model.bodies[0].design_body_id == document.bodies[0].id
            and model.bodies[0].transform == Transform(),
            "selected native cache, atom and actual neutral body are unresolved")
    CheckBrepOwners(model, document.bodies[0].id)
    require(len(model.regions) == len(model.shells) == len(model.shell_uses) == 1
            and not any(row.reversed for row in (*model.face_uses, *model.shell_uses)),
            "public shell has additional ownership or an alternate oriented use")
    bosses = tuple(row for row in document.feature_timeline if str(row.kind) == "extrusion")
    require(len(bosses) == len(document.sketches) == 1 and bosses[0].id == document.bodies[0].final_feature_id
            == f"sldprt:feature:{feature_id}", "public final feature is not the actual selected extrusion")
    boss, = bosses
    sketch, = document.sketches
    support, = (row for row in document.support_planes if row.id == sketch.support_plane_id)
    arc, = (row for row in sketch.entities if type(row.geometry) is CircleGeometry)
    extent = boss.definition
    require(support.name == "Front Plane" and support.transform == Transform()
            and boss.sketch_id == sketch.id and not (arc.construction or sketch.suppressed or boss.suppressed)
            and sketch.closed_profile_entity_ids == ((arc.id,),)
            and str(boss.operation) == "join" and str(extent.end_condition) == "blind"
            and not (extent.reversed or extent.symmetric) and extent.second_length is None
            and all(getattr(extent, field) is None for field in ("draft_angle", "offset", "second_draft_angle",
                    "second_offset", "direction", "second_end_condition"))
            and not (extent.up_to_reference or extent.second_up_to_reference)
            and extent.length.unit == "mm" and extent.length.value > 0 and arc.geometry.radius > 0,
            "selected child is outside the bounded forward blind circle support")
    circle = arc.geometry
    start = (circle.center.x, circle.center.y, 0.0)
    axis, reference = vector(support.transform.z_axis), vector(support.transform.x_axis)
    return model, boss, circle.radius, (start, shift(start, axis, extent.length.value)), axis, reference


def read_cylinder_roles(document, native):
    model, boss, radius, centers, design_axis, reference = read_design_cylinder(document, native)
    CheckCylSide(native)
    tree = ReadCylBodyTree(native.NodesValue)
    bind_public_inventory(model, tree)
    faces, surfaces, loops, coedges, edges, curves, vertices = (
        {row.id: row for row in getattr(model, name)} for name in
        ("faces", "surfaces", "loops", "coedges", "edges", "curves", "vertices")
    )
    side = faces[NativeId("face", native.FaceValue.IndexValue + 1)]
    carrier = surfaces[side.surface_id]
    require(type(carrier) is CylinderSurface and side.surface_id == NativeId("surface", native.SurfaceValue.IndexValue + 1),
            "selected face has another public carrier")
    carrier_axis = vector(carrier.axis)
    sign = 1 if dot(carrier_axis, design_axis) > 0 else -1
    near, far = (0, 1) if sign == 1 else (1, 0)
    carrier_origin = vector(carrier.origin)
    require(same_axis(carrier_axis, shift((0.0, 0.0, 0.0), design_axis, sign))
            and same_axis(vector(carrier.reference_direction), shift((0.0, 0.0, 0.0), reference, sign))
            and same_point(carrier_origin, centers[near])
            and same_point(carrier_origin, kernel_point(native.SurfaceValue, "pvec"))
            and same_axis(carrier_axis, ReadXmtVector(native.SurfaceValue, "axis"))
            and side.same_sense is (sign == 1)
            and same_value(carrier.radius, radius)
            and same_value(carrier.radius, 1000 * native.SurfaceValue.FieldsValue["radius"]),
            "lateral carrier orientation, radius or axial origin disagrees with the modeled cylinder")

    rims = {}
    feature = NativeNodeId(native.FeatureValue)
    epoch = DatumTime(native.LinkValue.ConfigValue.HeaderValue, feature)
    for cap in tuple(face for face in faces.values() if face is not side):
        plane = surfaces[cap.surface_id]
        nodes = native.NodesValue
        native_face = nodes[wire_index(cap.id)]
        native_plane = nodes[native_face.Integer("surface")]
        require(type(plane) is PlaneSurface
                and native_plane.IndexValue == wire_index(cap.surface_id),
                "cap surface has foreign identity")
        role = tuple(index for index, origin in enumerate(centers) if same_point(vector(plane.origin), origin))
        require(len(role) == 1 and role[0] not in rims
                and same_point(vector(plane.origin), kernel_point(native_plane, "pvec")),
                "cap origin disagrees with the two modeled end planes")
        role, = role
        require(same_axis(vector(plane.normal), design_axis) and same_axis(vector(plane.reference_direction), reference)
                and same_axis(vector(plane.normal), ReadXmtVector(native_plane, "normal"))
                and cap.same_sense is (role == 1), "cap carrier or outward sense is invalid")
        expected_selector = 1 if role == near else 0
        require(ReadCylWords(native.NodesValue, native_face) == (40, feature, epoch, 0, expected_selector, 0),
                "cap reference selector differs from carrier-relative role and producing feature")
        cap_loop, = (loops[identity] for identity in cap.loop_ids)
        cap_use, = (coedges[identity] for identity in cap_loop.coedge_ids)
        edge = edges[cap_use.edge_id]
        ring = curves[edge.curve_id]
        native_loop = nodes[native_face.Integer("loop")]
        native_fin = nodes[native_loop.Integer("halfedge")]
        native_edge = nodes[native_fin.Integer("edge")]
        native_ring = nodes[native_edge.Integer("curve")]
        require((wire_index(cap_loop.id), wire_index(cap_use.id), wire_index(edge.id), wire_index(ring.id))
                == (native_loop.IndexValue, native_fin.IndexValue, native_edge.IndexValue, native_ring.IndexValue),
                "cap loop, fin, edge and curve do not retain their exact kernel owners")
        require(type(ring) is CircleCurve and same_point(vector(ring.center), centers[role])
                and same_point(vector(ring.center), kernel_point(native_ring, "centre"))
                and same_axis(vector(ring.axis), design_axis) and same_axis(vector(ring.reference_direction), reference)
                and same_axis(vector(ring.axis), ReadXmtVector(native_ring, "normal"))
                and same_value(ring.radius, radius) and same_value(ring.radius, native_ring.FieldsValue["radius"] * 1000),
                "circular edge carrier differs from its actual cap plane")
        require(edge.start_vertex_id == edge.end_vertex_id and edge.start_vertex_id in vertices
                and not edge.degenerate and same_value(edge.start_parameter, 0.0) and same_value(edge.end_parameter, tau),
                "cap edge is not its complete closed circle")
        seam = vertices[edge.start_vertex_id]
        require(same_point(vector(seam.point), shift(centers[role], reference, radius)),
                "circular edge seam point differs from its physical curve")
        candidates = tuple(
            (loops[identity], coedges[use])
            for identity in side.loop_ids for use in loops[identity].coedge_ids
            if coedges[use].edge_id == edge.id
        )
        require(len(candidates) == 1, "cap edge does not have one reciprocal lateral use")
        (side_loop, side_use), = candidates
        native_side_fin = nodes[native_fin.Integer("other")]
        require(cap_loop.outer and side_loop.outer is (role == near)
                and len(side_loop.coedge_ids) == 1
                and (wire_index(side_loop.id), wire_index(side_use.id))
                == (native_side_fin.Integer("loop"), native_side_fin.IndexValue)
                and cap_use.reversed is (role == 0) and side_use.reversed is not cap_use.reversed,
                "cap and lateral loop incidence or edge direction disagree")
        rims[role] = Rim(cap.id, cap_loop.id, cap_use.id, side_loop.id, side_use.id,
                         edge.id, ring.id, seam.id, expected_selector)
    require(set(rims) == {near, far} and len({row.edge for row in rims.values()}) == len(edges) == 2
            and len({row.seam for row in rims.values()}) == len(vertices) == 2
            and {row.side_loop for row in rims.values()} == set(side.loop_ids),
            "rim and seam correspondence has ambiguous topology")
    return CylinderRoles(document, native, boss.id, side.id, radius, centers, design_axis, reference,
                         carrier_origin, sign, MappingProxyType(rims))


def match_cylinder_shapes(source, target):
    require(same_value(source.radius, target.radius)
            and all(same_point(left, right) for left, right in zip(source.centers, target.centers, strict=True))
            and same_axis(source.design_axis, target.design_axis)
            and same_axis(source.reference_direction, target.reference_direction),
            "generated radius, local extent or design frame differs from the source")
    return {
        source.side_face: target.side_face,
        **{source.rims[role].cap_face: target.rims[role].cap_face for role in source.rims},
    }


def read_native_endpoints(parent, parent_bytes, source):
    require(sha256(parent_bytes).hexdigest() == parent.source.sha256,
            "parent archive does not match the public source digest")
    archive = SldprtArchive.from_bytes(parent_bytes)
    link = ReadNativeLink(archive, 0)
    assembly = DecodeNativeAsm(archive, include_tessellation=False)
    context = MakeCylContext(PublicMateEnv(assembly, archive, {}, {}), link)
    mates = ReadMatesMut(archive.require(link.ConfigName + "-MatesList"), link.ResolvedValue)
    node, = mates.RootsValue
    mate_id = FieldInt(node.FieldsValue, "f08")
    wrappers = ReadRows(node.FieldsValue.get("f410"))
    require(len(wrappers) == 2 and FieldInt(node.FieldsValue, "f3b4") in (1, 2),
            "actual parent has an unqualified ordered cylindrical mate")
    active = tuple(RequireNode(row["o"], "moCylinderRef_w") for row in wrappers)
    require(all(FieldInt(row.FieldsValue, "f50") == 2 for row in active),
            "saved wrapper does not use the ordinary two-rim bounded carrier")
    endpoints = tuple(ReadCylEnd(context, source.native, row, mate_id, order) for order, row in enumerate(active))
    bounds = tuple((row.FieldsValue["fb0"], row.FieldsValue["fb8"]) for row in active)
    return endpoints, bounds, node.FieldsValue["f3b4"], node.FieldsValue["f4b8"]


def projected_rim_span(shape, axis):
    other_center = shape.centers[1 if shape.carrier_sign == 1 else 0]
    return dot(tuple((end - start) * 0.001 for end, start in zip(other_center, shape.carrier_origin, strict=True)), axis)


def map_source_endpoints(parent, parent_bytes, source, target):
    faces = match_cylinder_shapes(source, target)
    graph = parent.assembly
    proof = parent.metadata.get("solidworks.typed_mates_semantics", {})
    require(graph is not None and proof.get("status") == "admitted"
            and proof.get("full_selected_mate_graph") is True
            and len(graph.documents) == len(graph.mates) == 1 and len(graph.instances) == 2
            and graph.documents[0].document is source.child,
            "source parent does not own the exact independently verified child and mate")
    mate, = graph.mates
    instances = {row.id: row for row in graph.instances}
    entities = {row.id: row for row in graph.mate_entities}
    require(str(mate.kind) == "concentric" and str(mate.alignment) in ("aligned", "anti_aligned")
            and mate.suppressed is False and mate.driving is True and mate.value is None and not mate.parameter_ids
            and type(mate.attributes.get("rotation_locked")) is bool
            and set(mate.entity_ids) == set(entities) and len(mate.entity_ids) == len(entities) == 2,
            "source mate cannot supply one ordered concentric selection pair")
    native_ends, native_bounds, alignment, lock = read_native_endpoints(parent, parent_bytes, source)
    require(alignment == (1 if str(mate.alignment) == "aligned" else 2)
            and lock == int(mate.attributes["rotation_locked"]),
            "the portable mate does not retain its actual alignment and lock state")
    result = []
    for identity, actual, bounds in zip(mate.entity_ids, native_ends, native_bounds, strict=True):
        entity = entities[identity]
        require(len(entity.instance_path) == 1 and entity.instance_path[0] in instances
                and str(entity.kind) == "cylinder" and entity.source_entity_id == source.side_face,
                "mate endpoint does not select the actual lateral face on a direct occurrence")
        occurrence = instances[entity.instance_path[0]]
        attributes = entity.attributes
        require(entity.owner_definition_id == occurrence.owner_definition_id == graph.root_definition_id
                and attributes.get("typed_archive_selection") is True
                and attributes.get("native_child_sha256") == source.native.SourceHash
                and attributes.get("native_face_node_id") == source.native.FaceValue.Integer("node_id")
                and attributes.get("native_body_atom_id") == source.native.AtomValue
                and attributes.get("native_surface_feature_id") == NativeNodeId(source.native.FeatureValue)
                and attributes.get("native_surface_arc_permanent_marker") == source.native.ArcMarker
                and occurrence.id == f"sldasm:instance:{actual.ItemValue.object_id}"
                and occurrence.definition_id == f"sldasm:definition:{actual.ItemValue.definition_id}"
                and attributes.get("native_child_definition_id") == actual.ItemValue.definition_id
                and attributes.get("native_child_configuration_id") == actual.ItemValue.configuration_id
                and occurrence.configuration_name == actual.ItemValue.configuration_name == source.child.configurations[0].name
                and occurrence.reference_number == str(actual.ItemValue.reference_number)
                and occurrence.attributes.get("native_feature_id") == attributes.get("native_occurrence_feature_id") == actual.ItemValue.feature_id
                and same_value(entity.radius, source.radius), "mate portable and native owner references differ")
        frame = ReadAsmPlace(occurrence).FrameValue
        world_axis = tuple(attributes["stored_axis"])
        basis = (frame.AxisU, frame.AxisV, frame.NormalValue)
        placement = actual.ItemValue.transform
        require(all(same_axis(direction, placement[start:start + 3])
                    for direction, start in zip(basis, (0, 4, 8), strict=True))
                and dist(frame.OriginValue, placement[12:15]) <= 1e-12,
                "portable occurrence changed its underlying native placement")
        local_axis = tuple(dot(world_axis, direction) for direction in basis)
        axis_sign = 1 if dot(local_axis, source.design_axis) > 0.0 else -1
        require(same_axis(local_axis, shift((0.0, 0.0, 0.0), source.design_axis, axis_sign))
                and same_axis(local_axis, actual.LocalAxisValue)
                and same_axis(world_axis, actual.AxisValue),
                "source selected axis differs from its actual signed local and world wrapper")
        source_origin = tuple(attributes["stored_origin_m"])
        require(dist(source_origin, actual.OriginValue) <= 1e-12,
                "source carrier origin differs from its actual selected wrapper")
        expected_span = projected_rim_span(source, local_axis)
        require(bounds[0] == 0.0 and isclose(bounds[1], expected_span, rel_tol=1e-12, abs_tol=1e-12),
                "source signed wrapper bounds disagree with their reciprocal physical rims")
        target_origin = tuple(frame.OriginValue[index] + sum(direction[index] * coordinate * 0.001
                              for direction, coordinate in zip(basis, target.carrier_origin, strict=True))
                              for index in range(3))
        delta = tuple(a - b for a, b in zip(source_origin, target_origin, strict=True))
        require(dist(delta, shift((0.0, 0.0, 0.0), world_axis, dot(delta, world_axis))) <= 1e-12,
                "target origin is not on the original signed world carrier line")
        result.append({
            "entity": identity, "occurrence": occurrence.id, "reference_number": occurrence.reference_number,
            "source_face": entity.source_entity_id, "generated_face": faces[entity.source_entity_id],
            "world_axis": world_axis, "local_axis": local_axis,
            "stored_world_origin_m": source_origin, "generated_world_origin_m": target_origin,
            "source_axial_bounds_m": bounds, "generated_axial_bounds_m": (0.0, projected_rim_span(target, local_axis)),
        })
    require({row["occurrence"] for row in result} == set(instances)
            and isclose(dot(result[0]["world_axis"], result[1]["world_axis"]),
                        1 if str(mate.alignment) == "aligned" else -1, rel_tol=0.0, abs_tol=1e-10),
            "source occurrence order or signed alignment does not resolve")
    return tuple(result)
