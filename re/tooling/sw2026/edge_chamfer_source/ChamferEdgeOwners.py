from dataclasses import dataclass
from math import dist, isclose

from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeObList import MakeObList
from convert.adapters.solidworks.Archive.Construction.Model.MakeSelfComp import MakeSelfComp
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CompRefFields import CompRefFields
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from para.concentric.CylinderFace import make_feature_file
from para.prism.SdkPrismPartition import design_geometry

from BuildChamferBoundary import boundary, require


@dataclass(frozen=True, slots=True)
class EdgeSelection:
    endpoints: tuple
    faces: tuple
    selected_side: object


def node(name, fields):
    return ArchiveNode(RuntimeClass(name, 1), fields)


def same_endpoints(actual, wanted):
    return any(all(dist(a, b) < 1e-12 for a, b in zip(candidate, wanted, strict=True))
               for candidate in (actual, actual[::-1]))


def make_stock_selection(candidate, shape):
    boundary(shape)
    require(shape["body_id"] == candidate.PlanValue.BodyId,
            "chamfer must name the actual modeled stock body")
    body, surfaces, _, _, local_bounds = design_geometry(candidate)
    proposed = [list(interval) for interval in shape["stock_bounds_m"]]
    actual = tuple(tuple(0.001 * getattr(point, axis) for point in (local_bounds.minimum, local_bounds.maximum))
                   for axis in "xyz")
    require(all(dist(pair, want) < 1e-12 for pair, want in zip(actual, proposed, strict=True)),
            "chamfer stock bounds must be owned by the actual generated blind boss")
    along = shape["edge_axis"]
    side = shape["distance_axis"]
    picks = tuple(tuple(actual[axis][station if axis == along else shape["corner"][str(axis)]]
                        for axis in range(3)) for station in (0, 1))
    vertices = {vertex.id: tuple(0.001 * getattr(vertex.point, n) for n in "xyz") for vertex in body.vertices}
    edges = [edge for edge in body.edges if same_endpoints(
        (vertices[edge.start_vertex_id], vertices[edge.end_vertex_id]), picks)]
    require(len(edges) == 1, "user selection must name one actual boss edge")
    edge, = edges

    by_edge = {}
    by_use = {}
    loops = {loop.id: loop.coedge_ids for loop in body.loops}
    for face in body.faces:
        loop_id, = face.loop_ids
        for use_id in loops[loop_id]:
            by_use[use_id] = (face.id, loops[loop_id])
    for use in body.coedges:
        by_edge.setdefault(use.edge_id, []).append(use)
    for uses in by_edge.values():
        require(len(uses) == 2 and {use.reversed for use in uses} == {True, False},
                "ordinary edge roles require two reciprocal signed fins")
    uses = {use.id: use for use in body.coedges}
    opposite = {use.id: other.id for a, b in by_edge.values() for use, other in ((a, b), (b, a))}
    left = next(use.id for use in by_edge[edge.id] if not use.reversed)
    face_id, ring = by_use[left]
    at = ring.index(left)
    role_ids = (face_id, by_use[opposite[left]][0],
                by_use[opposite[ring[at - 1]]][0], by_use[opposite[ring[(at + 1) % len(ring)]]][0])
    require(len(set(role_ids)) == 4, "generated chamfer edge has ambiguous incident or endpoint faces")

    carriers = {surface.id: surface for surface in body.surfaces}
    faces = {face.id: face for face in body.faces}
    normals = [carriers[faces[owner].surface_id].normal for owner in role_ids[:2]]
    inner = tuple(owner for owner, normal in zip(role_ids[:2], normals, strict=True)
                  if isclose(abs(getattr(normal, "xyz"[side])), 1.0, abs_tol=1e-12))
    require(inner == (role_ids[0],) and set(uses) == set(by_use),
            "authored chamfer distance side differs from the positive fin's first face")
    return EdgeSelection(picks, tuple(surfaces[owner] for owner in role_ids), surfaces[inner[0]])


def make_representations(candidate, feature, atom, selection, headers):
    model = candidate.SystemValue.RootValue
    boss = candidate.BossValue.FeatureValue
    require(feature.FieldsValue.get("owner") is model
            and len({feature.FieldsValue["f08"], boss.FieldsValue["f08"]}) == 2
            and atom.FieldsValue["f12c"] == boss.FieldsValue["f08"]
            and atom.FieldsValue["f130"] == feature.FieldsValue["f08"]
            and boss.FieldsValue["f528"]["items"][0]["o"] is atom is feature.FieldsValue["f538"]
            and model.FieldsValue["fd88"]["atoms"][0]["o"] is atom,
            "chamfer references need actual stock producer, modified atom and result feature")
    historical_file = make_feature_file(candidate)
    require(historical_file.FieldsValue["shared"] and historical_file is not candidate.HeaderValue.FieldsValue["f38"],
            "historical surface owners require their own filed object and actual shared location")
    events = {}
    for owner in (boss, feature):
        identity = owner.FieldsValue["f08"]
        config, top = (DatumTime(header, identity) for header in headers)
        require(config == top and config != 2592000,
                "both generated headers must bind the actual feature creation event")
        events[owner] = config

    def record(class_name, owner, extra=(), *, direct=False):
        reference = node("moFR_c", {"f08": historical_file,
                                    "f10": {"f00": owner.FieldsValue["f08"], "f08": events[owner]}})
        return node(class_name, {"f10": {"f08": owner if direct else None, "f10": reference}, **dict(extra)})

    def stock(role):
        if role.cap:
            return record("moEndFaceSurfIdRep_c", boss, (("f38", role.number), ("f3c", 0)))
        return record("moFromSktEntSurfIdRep_c", boss, (("f38", role.number),))

    selected_support = tuple(stock(role) for role in selection.faces)
    detached_support = tuple(stock(role) for role in selection.faces)
    result = (
        record("moSurfaceIdRep_c", feature, direct=True),
        record("moFilletSurfIdRep_c", feature, (("f38", 1),), direct=True),
    )
    return selected_support, detached_support, result, historical_file


def edge_refs(base, extra, index, model):
    def cold_edge(support):
        return node("moEdgeRef_c", {
            "f60": 1, "f64": 0, "f08": len(support), "fe8": 0x200, "f70": 0,
            "f28": 1e100, "f30": 1e100, "f40": None, "f10": [{"f08": rep} for rep in support],
            "f48": 0, "nd0": 0, "fd0": [], "fec": 19000, "has_f18": 0,
        })

    def wrap(reference):
        return node("moCompEdge_c", CompRefFields(MakeSelfComp(model)) | {
            "f18": index, "f1c": index, "has_alias": 0, "fe8": reference, "ff0": None,
            "f188": 0, "f158": dict.fromkeys("xyz", 0.0), "f170": dict.fromkeys("xyz", 0.0),
            "f18c": 0, "n140": 0, "f130": [],
        })

    return tuple(wrap(cold_edge(support)) for support in (base, extra))


def make_edge_fields(candidate, feature, atom, selection, headers):
    base, extra, result, locator = make_representations(candidate, feature, atom, selection, headers)
    selected, other = edge_refs(base, extra, atom.FieldsValue["f140"], candidate.SystemValue.RootValue)
    picked = selected.FieldsValue["fe8"]
    edges = node("suObList", {"n": 1, "items": [{"o": selected}]})
    keeper = {"f18": {"n": len(result), "items": [{"id": {"f08": rep}} for rep in result]},
              "ff0": {"n": 1, "items": [{"o": picked}]}}
    return {"f880": keeper, "f888": edges, "f890": node("suObList", MakeObList()),
            "f898": node("suObList", MakeObList()), "f8a8": other}, locator
