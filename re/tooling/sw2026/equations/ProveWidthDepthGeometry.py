from argparse import ArgumentParser
from contextlib import contextmanager
from dataclasses import replace
from importlib import import_module
from itertools import combinations, product
import json
from math import isclose, prod
from pathlib import Path
import sys


HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from ProveLocalWidthDepthRead import ACTUAL, MANAGED, PLAIN, RESOLVED, ROOT, digest, open_read, parameters, require


OWNERS = ROOT / "src/convert/adapters/solidworks/Core/TypedResolved"
REFERENCE = ACTUAL[2]
SAVED_REFERENCE = ACTUAL[3]
NO_PAYLOAD = "SLDPRT contains no readable Parasolid payload"


@contextmanager
def patch(module, name, replacement):
    original = getattr(module, name)
    setattr(module, name, replacement)
    try:
        yield
    finally:
        setattr(module, name, original)


def xyz(point):
    return point.x, point.y, point.z


def close(actual, expected):
    return isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-9)


def measure(doc, expected):
    from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface

    require(len(doc.bodies) == 1 and doc.brep is not None, "strict SDK read needs its real body")
    brep = doc.brep
    require(tuple(len(getattr(brep, field)) for field in ("bodies", "shells", "faces", "edges", "vertices"))
            == (1, 1, 6, 12, 8) and brep.shells[0].closed and not brep.validate(frozenset((doc.bodies[0].id,))),
            "decoded solid topology is incomplete")
    points = {vertex.id: xyz(vertex.point) for vertex in brep.vertices}
    axes = tuple(sorted(set(values)) for values in zip(*points.values()))
    require(all(len(axis) == 2 for axis in axes)
            and set(points.values()) == set(product(*axes)), "decoded vertices are not the eight physical prism corners")
    lower = tuple(axis[0] for axis in axes)
    extents = tuple(axis[1] - axis[0] for axis in axes)
    require(all(close(value, 0.0) for value in lower)
            and all(close(value, target) for value, target in zip(extents, expected)), "decoded solid dimensions differ")
    edges = {frozenset((points[edge.start_vertex_id], points[edge.end_vertex_id])) for edge in brep.edges}
    require(len(edges) == 12 and all(sum(a != b for a, b in zip(*pair)) == 1 for pair in edges),
            "decoded solid edges do not bound the physical prism")
    surfaces = {surface.id: surface for surface in brep.surfaces}
    planes = [surfaces[face.surface_id] for face in brep.faces]
    require(all(isinstance(plane, PlaneSurface) for plane in planes), "decoded prism has a nonplanar face")
    placement = set()
    for plane in planes:
        active = [index for index, value in enumerate(xyz(plane.normal)) if not close(value, 0.0)]
        require(len(active) == 1, "decoded face does not align with the actual prism")
        (axis,) = active
        origin = xyz(plane.origin)[axis]
        (side,) = [index for index, value in enumerate(axes[axis]) if close(value, origin)]
        placement.add((axis, side))
    require(placement == set(product(range(3), range(2))), "decoded faces omit a physical prism side")
    volume = prod(extents)
    area = 2.0 * sum(left * right for left, right in combinations(extents, 2))
    centre = tuple(sum(axis) / 2.0 for axis in axes)
    require(close(volume, prod(expected))
            and close(area, 2.0 * sum(left * right for left, right in combinations(expected, 2)))
            and all(close(value, target / 2.0) for value, target in zip(centre, expected)),
            "measured boundary mass properties differ from independent dimensions")
    return {"body_count": len(brep.bodies), "face_count": len(brep.faces), "edge_count": len(brep.edges),
            "vertex_count": len(brep.vertices), "volume_mm3": volume, "area_mm2": area, "centre_mm": centre,
            "bounds_mm": (lower, tuple(axis[1] for axis in axes))}


def read_solid(managed, label, relative, expected_sha, lengths, cold, related):
    doc = open_read(managed / relative, expected_sha)
    ref = ("sldprt:parameter:18:D1",) if related else ()
    _, _, depth = parameters(
        doc, (18, 21), lengths, "derived" if related else "driving", ref, '"D1@Sketch1" / 2' if related else None,
    )
    reconstructed = [diag for diag in doc.diagnostics if diag.code == "sldprt.brep_reconstructed"]
    proof = doc.metadata[RESOLVED].get("local_width_depth_equation")
    require(bool(proof) == related, "local equation did not retain its expected typed ownership")
    require(len(doc.brep_payloads) == (0 if cold else 3) and len(reconstructed) == int(cold),
            "unexpected reconstruction or native geometry payload count")
    measured = measure(doc, lengths)
    if cold:
        (diagnostic,) = reconstructed
        topology = doc.bodies[0].topology
        require(diagnostic.attributes["method"] == "typed_parametric_rectangular_prism"
                and not diagnostic.attributes["native_kernel_identity"]
                and diagnostic.attributes["depth_owner"] == depth.attributes["typed_archive_owner"],
                "strict shared prism did not use the assigned live depth owner")
        require(topology.valid and close(topology.volume, measured["volume_mm3"])
                and close(topology.surface_area, measured["area_mm2"]), "SDK topology summary diverges from actual boundary")
    return label, {"sha256": expected_sha, "cold_geometry": cold, "native_payloads": len(doc.brep_payloads),
                   "related": related, **measured}


def link_inventory(module):
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismClasses import KPrismClasses

    seen = []
    original = module.CheckPrismScope

    def observe(link, manager, model, cold):
        relation = model.WidthDepth
        if relation is not None:
            require(relation.LinkValue is link and cold is None, "cold equation lost its original proof graph")
            config = link.ConfigValue.MapValue.EntriesValue
            resolved = link.ResolvedValue.MapValue.EntriesValue
            require(link.ResolvedValue.MapBase == link.ConfigValue.MapValue.CounterValue
                    and len(resolved) >= len(config)
                    and all(left.IndexValue == right.IndexValue and left.EntryValue is right.EntryValue
                            for left, right in zip(config, resolved)), "linked map did not inherit its actual prefix")
            outside = frozenset(
                row.EntryValue for row in (*resolved, *manager.MapValue.EntriesValue)
                if isinstance(row.EntryValue, ArchiveNode) and row.EntryValue.ClassValue.NameValue not in KPrismClasses
            )
            require(outside == relation.RelationNodes, "strict new owner inventory differs from original local equation")
            seen.append({"config_counter": link.ConfigValue.MapValue.CounterValue,
                         "resolved_counter": link.ResolvedValue.MapValue.CounterValue, "prefix_entries": len(config),
                         "relation_node_inventory": sorted((node.IndexValue, node.ClassValue.NameValue) for node in outside)})
        return original(link, manager, model, cold)

    return seen, patch(module, "CheckPrismScope", observe)


def expression_nodes(link):
    root = link.ConfigValue.RootValue
    (row,) = root.FieldsValue["f9d0"].FieldsValue["f58"]["items"]
    relation = row["o"]
    left = relation.FieldsValue["f58"].FieldsValue["f10"]["items"][0]["o"]
    right = relation.FieldsValue["f60"].FieldsValue["f10"]["items"][1]["o"]
    return relation, left.FieldsValue["f80"], right.FieldsValue["f80"]


def graph_fault(link, fault):
    from convert.adapters.solidworks.Archive.Maps.MapEntry import MapEntry
    from convert.adapters.solidworks.Archive.Maps.MapSnapshot import MapSnapshot
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
    from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
    from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadLineDims import ReadLineDims

    relation, depth, width = expression_nodes(link)
    clone = width.FieldsValue["f58"]
    if fault == "height_clone":
        profile = IndexFeatures(link)[18]
        width_value, height = ReadLineDims(profile.FieldsValue["pd_f80"], link).DriverValues
        require(clone.FieldsValue["ff0"] is width_value.HandleValue.FieldsValue["ff0"]
                is height.HandleValue.FieldsValue["ff0"] and clone.FieldsValue["ff8"] == width_value.IndexValue,
                "the injected ordinal must cross to the actual height owner")
        clone.FieldsValue["ff8"] = height.IndexValue
        width.FieldsValue["fb0"] = height.MetresValue
    elif fault == "cached_width" or fault == "stale_after_proof":
        width.FieldsValue["fb0"] += 0.001
    elif fault == "live_depth":
        distance = depth.FieldsValue["f58"].FieldsValue["ff0"]
        parameter = distance.FieldsValue["f28"]
        parameter.FieldsValue["f58"] += 0.001
        depth.FieldsValue["fb0"] = parameter.FieldsValue["f58"]
    elif fault == "wrong_expression":
        relation.FieldsValue["f10"] = relation.FieldsValue["f10"].removesuffix(" / 2") + " / 3"
    else:
        require(fault == "detached_relation_node", "unrecognized disclosed fault")
        old = link.ResolvedValue.MapValue
        extra = ArchiveNode(RuntimeClass("moRelValue_c", 1), {}, IndexValue=old.CounterValue)
        mapped = MapSnapshot(old.CounterValue + 1, (*old.EntriesValue, MapEntry(old.CounterValue, extra)))
        return replace(link, ResolvedValue=replace(link.ResolvedValue, MapValue=mapped))
    return link


def strict_refusal(managed):
    from convert.adapters.solidworks.Container.Container import SldprtFormatError

    path, expected_sha = managed / REFERENCE[1], REFERENCE[2]
    try:
        open_read(path, expected_sha)
    except SldprtFormatError as error:
        require(str(error) == NO_PAYLOAD and digest(path) == expected_sha, "strict fail-closed contract differs")
        return str(error)
    raise ValueError("unqualified reference produced strict geometry")


def fault_receipt(managed, geometry, equation, fault, expected_reason):
    graph_read = equation.ReadNativeLink
    read_relation = equation.ReadWidthDepth
    geom_scope = geometry.CheckPrismScope
    seen = []
    causes = []

    def link_with_fault(*args, **kwargs):
        link = graph_read(*args, **kwargs)
        require(kwargs["RelationConfig"] == "modeled default", "fault entered a different config")
        if fault not in ("stale_after_proof", "legacy_text_mismatch"):
            seen.append(fault)
            return graph_fault(link, fault)
        return link

    def watch_relation(*args):
        try:
            return read_relation(*args)
        except ValueError as error:
            causes.append(str(error))
            raise

    def watch_scope(link, manager, model, cold):
        if fault == "stale_after_proof":
            require(model.WidthDepth.LinkValue is link, "post-proof fault did not reach the retained exact graph")
            graph_fault(link, fault)
            seen.append(fault)
        if fault == "legacy_text_mismatch":
            require(model.WidthDepth.LinkValue is link, "legacy text mismatch lost its real typed proof")
            (row,) = model.equations
            model = replace(model, equations=(replace(row, source=row.source + " + 1"),))
            seen.append(fault)
        try:
            return geom_scope(link, manager, model, cold)
        except ValueError as error:
            causes.append(str(error))
            raise

    with (patch(equation, "ReadNativeLink", link_with_fault), patch(equation, "ReadWidthDepth", watch_relation),
          patch(geometry, "CheckPrismScope", watch_scope)):
        public_error = strict_refusal(managed)
    require(seen == [fault] and causes == [expected_reason], "strict route refused for the wrong reason")
    return fault, {"source_sha256": REFERENCE[2], "internal_refusal": causes[0], "strict_public_error": public_error}


def prefix_receipt(managed, link_module):
    original = link_module.ReadResolvedMut
    seen = []
    causes = []

    def invalid_base(data, version, seed, context):
        actual = int.from_bytes(data[:4], "little")
        require(actual == seed.CounterValue, "baseline is already detached from its configuration")
        seen.append((actual, actual + 1))
        altered = (actual + 1).to_bytes(4, "little") + data[4:]
        try:
            return original(altered, version, seed, context)
        except ValueError as error:
            causes.append(str(error))
            raise

    with patch(link_module, "ReadResolvedMut", invalid_base):
        public_error = strict_refusal(managed)
    require(seen == [(163, 164)]
            and causes == ["resolved archive base differs from its actual configuration snapshot"],
            "stored prefix was not rejected by the real linked parser")
    return {"source_sha256": REFERENCE[2], "base_before_after": seen[0],
            "internal_refusal": causes[0], "strict_public_error": public_error}


def source_receipt(managed, geometry):
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.IsCacheAbsent import IsCacheAbsent

    adapter = import_module("convert.adapters.solidworks.Core.Adapter")
    prepare = adapter.ReadNoCache
    _, relative, expected_sha, _, _ = PLAIN[0]
    plain_path = managed / relative
    require(digest(plain_path) == expected_sha, "unrelated disclosure hash changed")
    unmatched = SldprtArchive.from_bytes(plain_path.read_bytes())
    require(IsCacheAbsent(unmatched), "mismatched source must otherwise qualify as cache absent")
    seen = []

    def different_source(archive, model, body_id):
        require(model.WidthDepth.SourceValue is archive and unmatched is not archive,
                "source identity injection did not preserve the real original proof")
        seen.append(expected_sha)
        return prepare(unmatched, model, body_id)

    def unexpected_scope(*args):
        raise AssertionError("mismatched source reached the ordinary prism scope")

    with patch(adapter, "ReadNoCache", different_source), patch(geometry, "CheckPrismScope", unexpected_scope):
        public_error = strict_refusal(managed)
    require(seen == [expected_sha], "mismatched source never reached strict read")
    return {"source_sha256": REFERENCE[2], "substituted_archive_sha256": seen[0],
            "strict_public_error": public_error, "entered_prism_scope": False}


def compare_saved_native(solids):
    path = ROOT / "re/solidworks/measurements/2026/WidthDepthSameLocatorNative01.json"
    saved = json.loads(path.read_text())["arms"]
    for arm, label in (("Plain", "native_saved_plain"), ("Reference", "native_saved_reference")):
        state = saved[arm]["states"]["fresh_reopen"]
        metrics = state["mass_properties"]
        sdk = solids[label]
        require(saved[arm]["saved_sha256"] == sdk["sha256"] and state["body_count"] == sdk["body_count"]
                and close(sdk["volume_mm3"], metrics["volume"] * 1e9)
                and close(sdk["area_mm2"], metrics["area"] * 1e6)
                and all(close(actual, prior * 1000.0) for actual, prior in zip(sdk["centre_mm"], metrics["com"])),
                "decoded saved boundary differs from the committed native measurement")
    return digest(path)


def main():
    parser = ArgumentParser()
    parser.add_argument("--disclosed-root", type=Path, default=MANAGED)
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT / "src"))
    geometry = import_module("convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadNoCache")
    equation = import_module("convert.adapters.solidworks.Core.TypedResolved.Equations.TryWidthDepth")
    link_module = import_module("convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink")
    managed = args.disclosed_root
    observed, witness = link_inventory(geometry)
    with witness:
        solids = dict(
            read_solid(managed, label, relative, sha, lengths, payloads == 0, False)
            for label, relative, sha, lengths, payloads in PLAIN
        )
        solids.update(read_solid(managed, row[0], row[1], row[2], row[4], row[9] is None, True)
                      for row in (REFERENCE, SAVED_REFERENCE))
    require(len(observed) == 1, "native cached reference or unrelated plain control entered the exception")
    control, candidate = solids["generated_plain"], solids["generated_reference"]
    require(all(control[key] == candidate[key] for key in ("volume_mm3", "area_mm2", "centre_mm", "bounds_mm")),
            "same-size disclosed plain and reference did not reconstruct identical geometry")
    faults = dict(
        fault_receipt(managed, geometry, equation, fault, reason) for fault, reason in (
            ("height_clone", "local equation dimension does not alias its exact live owner"),
            ("cached_width", "local equation dimension has unqualified wrapper state"),
            ("live_depth", "local width-depth equation disagrees with live depth"),
            ("wrong_expression", "native relation is outside the enabled local width-depth expression"),
            ("detached_relation_node", "cache free prism has an unsupported native owner"),
            ("stale_after_proof", "local equation dimension has unqualified wrapper state"),
            ("legacy_text_mismatch", "cache free part has unsupported configuration or equation intent"),
        )
    )
    faults["resolved_prefix"] = prefix_receipt(managed, link_module)
    faults["mismatched_source_object"] = source_receipt(managed, geometry)
    files = (
        HERE, HERE.with_name("ProveLocalWidthDepthRead.py"),
        *(OWNERS / "Equations" / (name + ".py")
          for name in ("ReadEqTokens", "ReadWidthDepth", "TryWidthDepth", "WidthDepthLink")),
        *(OWNERS / "Geometry" / (name + ".py")
          for name in ("CheckGeometryState", "CheckPrismScope", "PrismNodes", "ReadNoCache")),
    )
    report = {
        "schema": "kit.sw2026.width-depth-cache-free-sdk-read.v1",
        "strict_reads": solids, "linked_scope": observed[0], "faults": faults,
        "compared_committed_native_receipt_sha256": compare_saved_native(solids),
        "reader_and_tool_sha256": {str(path.relative_to(ROOT)): digest(path) for path in files},
        "runtime_native_operations": 0, "fixture_file_mutations": 0, "heldout_inputs_read": False,
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
