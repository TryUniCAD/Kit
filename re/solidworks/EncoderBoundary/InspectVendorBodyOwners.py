from argparse import ArgumentParser
from dataclasses import fields, replace
from hashlib import sha256
import json
from math import isclose
from pathlib import Path
from subprocess import check_output
import sys


REVISION = "c0a401a607759fb0c2589647c2a22af65ebb7ce1"


def digest(raw):
    return sha256(raw).hexdigest()


def cases(record_path):
    raw = record_path.read_bytes()
    report = json.loads(raw)
    if report["passed"] is not True:
        raise ValueError("the authoring record did not pass")
    if "authored" in report:
        for name, row in sorted(report["authored"].items()):
            if Path(name).name != name or Path(name).suffix.casefold() != ".sldprt":
                raise ValueError("unexpected authoring record file name")
            yield Path(name).stem, record_path.parent / name, row["sha256"], digest(raw), row["body"]
    else:
        for name, row in sorted(report["samples"].items()):
            if not name.isascii() or not name.isalpha():
                raise ValueError("unexpected authoring record sample name")
            yield name, record_path.parent / name / "Prism.SLDPRT", row["sha256"], digest(raw), row["api_observation"]


def verify_dependency(root):
    revision = check_output(("git", "rev-parse", "HEAD"), cwd=root).decode().strip()
    changes = check_output(("git", "status", "--porcelain", "--untracked-files=no"), cwd=root)
    if revision != REVISION or changes:
        raise ValueError("body proof requires the unmodified pinned PR121 SDK")
    sys.path.insert(0, str(root / "src"))


def directed_rings(model, design_id):
    from convert.adapters.solidworks.Core.Partition.PartMassRings import ReadMassRings
    from convert.adapters.solidworks.Core.TypedResolved.BodyNames.CheckBrepOwners import CheckBrepOwners
    from convert.adapters.solidworks.Core.TypedResolved.Chamfers.Warm.CheckWarmGeo import CheckWarmLines, CheckWarmPlanes

    CheckBrepOwners(model, design_id)
    rings = ReadMassRings(model)
    CheckWarmLines(model)
    CheckWarmPlanes(model, rings)
    return tuple(tuple((point.x, point.y, point.z) for point in ring) for ring in rings)


def match_rings(observed, expected):
    from convert.adapters.solidworks.Core.TypedResolved.Chamfers.Warm.CheckWarmSolid import IsSameWarmRing

    matches = tuple(
        tuple(index for index, other in enumerate(expected) if IsSameWarmRing(ring, other))
        for ring in observed
    )
    return (
        len(observed) == len(expected)
        and all(len(row) == 1 for row in matches)
        and len(set(matches)) == len(expected)
    )


def active_owner(link, nodes, design):
    from convert.adapters.solidworks.Archive.Partition.CheckXmtAttrs import CheckXmtAttrs
    from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
    from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
    from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyAtom import ReadBodyAtom
    from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyAttrs import ReadBodyAttrs
    from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyAuthor import ReadBodyAuthor
    from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadKernelName import ReadKernelName

    world = RequireXmt(nodes, 1, 101)
    body_ids = WalkXmtChain(nodes, world.Integer("body"), 12, OwnerField="owner", OwnerValue=1)
    if len(body_ids) != 1 or set(body_ids) != {node.IndexValue for node in nodes.values() if node.KindValue == 12}:
        raise ValueError("the active world does not own exactly one body")
    body = nodes[body_ids[0]]
    if body.Integer("body_type") != 1 or any(
        body.Integer(name) for name in ("child", "ref_instance", "lattice", "mesh", "polyline")
    ):
        raise ValueError("the active body has an unqualified alternate representation")
    CheckXmtAttrs(nodes, body)
    attrs = ReadBodyAttrs(nodes, body)
    label, explicit = ReadKernelName(nodes, attrs, ReadBodyAuthor(link))
    atom, feature_id = ReadBodyAtom(link, nodes, attrs, label, explicit)
    if design.final_feature_id != f"sldprt:feature:{feature_id}":
        raise ValueError("the partition tags do not bind the public final feature")
    return body, {
        "label": label, "explicit_label": explicit, "feature_id": feature_id,
        "atom_slot": atom.IndexValue, "body_slot": body.IndexValue,
        "atom_identity_fields": {key: atom.FieldsValue[key] for key in ("f12c", "f130", "f140", "f180", "f1b0")},
        "attributes": sorted(attrs),
    }


def expected_prism(link, document, design):
    from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
    from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyOwner import ReadBodyOwner
    from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
    from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
    from interchange.geometry.Models.GeometryCurves import LineGeometry

    owner = ReadExtrude(link, ReadBodyOwner(link, None), IndexFeatures(link))
    if owner.ModeValue != "blind" or owner.IsReversed or owner.SecondValue is not None:
        raise ValueError("the actual feature is outside the plain forward blind profile")
    driver, = document.parameters
    if driver.owner_id != design.final_feature_id or driver.value.unit != "mm" or driver.role != "driving":
        raise ValueError("typed D1 is not bound to the proven final feature")
    depth = owner.RequireDepth().DepthValue.value_mm
    if depth != driver.value.value:
        raise ValueError("typed D1 and its native field disagree")
    sketch, = document.sketches
    contour, = sketch.closed_profile_entity_ids
    if sketch.constraints or not 3 <= len(contour) == len(sketch.entities) <= 64:
        raise ValueError("the source does not own a single bounded plain line loop")
    planes = [value for value in document.support_planes if value.id == sketch.support_plane_id]
    if len(planes) != 1 or planes[0].name != "Front Plane":
        raise ValueError("the source does not own an ordinary Front datum")
    by_id = {entity.id: entity for entity in sketch.entities}
    profile = tuple(by_id[key] for key in contour)
    if any(type(entity.geometry) is not LineGeometry or entity.construction or entity.fixed for entity in profile):
        raise ValueError("the contour has unsupported entity semantics")
    expected, volume, area, bounds = BuildPrism(
        design.id, planes[0].transform, tuple(row.geometry for row in profile), 0.0, depth
    )
    return expected, volume, area, bounds, depth, len(profile)


def inspect(raw):
    from convert import open_document
    from convert.Geometry.Parasolid import DecodeBrepModel
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Partition.PartMass import ReadPartMass
    from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyFaces import ReadBodyFaces
    from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyKernel import ReadBodyKernel
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    document = open_document(raw, source_format="solidworks.sldprt", strict=True)
    design, = document.bodies
    archive = SldprtArchive.from_bytes(raw, "<comparison>")
    link = ReadNativeLink(archive, 0)
    name = link.ConfigName + "-Partition"
    payloads, nodes, marks = ReadBodyKernel(archive.require(name), name)
    body, owner = active_owner(link, nodes, design)
    active = DecodeBrepModel(payloads[0].data)
    if active is None or document.brep is None:
        raise ValueError("the active or public boundary was not decoded")
    attached, = [value for value in document.brep_payloads if value.source_stream == name and value.kind == "partition"]
    if attached.data != payloads[0].data or attached.sha256 != payloads[0].sha256:
        raise ValueError("the public partition does not select the actual active bytes")
    expected, volume, area, bounds, depth, sides = expected_prism(link, document, design)
    face_ids = ReadBodyFaces(nodes, body, sides + 2)
    expected_rings = directed_rings(expected, design.id)
    active_rings = directed_rings(active, design.id)
    public_rings = directed_rings(document.brep, design.id)
    if not match_rings(active_rings, expected_rings) or not match_rings(public_rings, expected_rings):
        raise ValueError("the selected partition, public geometry and typed prism disagree")
    counts = [len(active.faces), len(active.edges), len(active.vertices)]
    if len(face_ids) != counts[0] or counts != [sides + 2, 3 * sides, 2 * sides]:
        raise ValueError("the partition topology differs from a single closed prism")
    public_unbound = replace(document.brep, bodies=tuple(
        replace(value, design_body_id="") for value in document.brep.bodies
    ))
    mass = ReadPartMass(active, bounds)
    if mass is None or abs(mass.Volume - volume) > 1e-7:
        raise ValueError("the selected partition disagrees with the typed prism volume")
    return {
        "owner": owner, "rollback_mark_ids": marks, "profile_lines": sides, "depth_mm": depth,
        "partition_sha256": digest(payloads[0].data), "volume_mm3": mass.Volume,
        "surface_area_expected_mm2": area, "centroid_mm": mass.Centroid,
        "faces_edges_vertices": counts,
        "directed_boundary_match": True,
        "public_equals_partition": document.brep == active,
        "public_without_design_id_equals_partition": public_unbound == active,
        "changed_public_brep_collections": [
            field.name for field in fields(active)
            if getattr(public_unbound, field.name) != getattr(active, field.name)
        ],
        "changed_public_kernel_body_fields": [
            field.name for field in fields(active.bodies[0])
            if getattr(public_unbound.bodies[0], field.name) != getattr(active.bodies[0], field.name)
        ],
    }


def compare_oracle(observed, inferred):
    numbers = (
        (observed["depth_m"] * 1000, inferred["depth_mm"]),
        (observed["volume_m3"] * 1e9, inferred["volume_mm3"]),
        (observed["area_m2"] * 1e6, inferred["surface_area_expected_mm2"]),
        *zip((value * 1000 for value in observed["centre_of_mass_m"]), inferred["centroid_mm"], strict=True),
    )
    if (
        observed["bodies"] != 1 or observed["dimension_driving"] is not True
        or [observed[key] for key in ("faces", "edges", "vertices")] != inferred["faces_edges_vertices"]
        or any(not isclose(first, second, rel_tol=1e-9, abs_tol=1e-8) for first, second in numbers)
    ):
        raise ValueError("the selected partition or live depth differs from the independent API")
    return len(numbers) + 5


def main():
    parser = ArgumentParser(description="Measure exact active body ownership and directed boundaries")
    parser.add_argument("--dependency-root", required=True, type=Path)
    parser.add_argument("--source-record", required=True, type=Path, action="append")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    verify_dependency(args.dependency_root.resolve())
    report = {}
    for path in args.source_record:
        for case, source, expected, record_hash, observed in cases(path):
            raw = source.read_bytes()
            if case in report or digest(raw) != expected:
                raise ValueError(f"{case} duplicate or different from its acquired native digest")
            row = {"source_sha256": expected, "source_record_sha256": record_hash}
            try:
                inferred = inspect(raw)
                row.update(inferred)
                row["api_comparisons_passed"] = compare_oracle(observed, inferred)
            except (TypeError, ValueError, KeyError) as error:
                row["refused"] = f"{type(error).__name__}: {error}"
            report[case] = row
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump({"dependency": REVISION, "cases": report}, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


if __name__ == "__main__":
    main()
