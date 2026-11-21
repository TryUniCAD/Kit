from collections import Counter
from hashlib import sha256
from io import BytesIO
from itertools import combinations, product
import json
from math import dist, isclose, prod
import os
from pathlib import Path
from subprocess import check_output, run
import sys
from tarfile import open as open_tar
from tempfile import TemporaryDirectory
from xml.etree.ElementTree import fromstring
from zipfile import ZipFile


REVISION = "06bea18f6f9f139be396e391aba2f2e27c4a8382"
LOCK = "4166c533b004dabae3f6e459bb5b66a3f9986eccef36f5fa6033b966e7abd837"
NAMES = ("Baked01.FCStd", "Baked02.FCStd", "ParametricControl.FCStd")
LENGTHS = {"Length", "Width", "Height"}
RUNTIME_MODULES = {"freecad", "freecadgui", "part", "sketcher", "win32com", "pythoncom"}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(data):
    return sha256(data).hexdigest()


def checked_file(path, expected):
    require(path.is_file() and not path.is_symlink(), "invalid disclosed input file")
    raw = path.read_bytes()
    require(digest(raw) == expected, "disclosed input SHA-256 differs")
    return raw


def properties(element):
    rows = element.findall("./Properties/Property")
    result = {row.attrib["name"]: row for row in rows}
    require(len(result) == len(rows), "duplicate object property")
    return result


def physical_owner(path, expected):
    raw = checked_file(path, expected["file_sha256"])
    baked = expected["standalone_baked"]
    with ZipFile(BytesIO(raw)) as archive:
        xml = archive.read("Document.xml")
        require(digest(xml) == expected["document_xml_sha256"], "disclosed Document.xml SHA-256 differs")
        root = fromstring(xml)
        require(root.tag == "Document" and root.get("SchemaVersion") == "4"
                and root.get("ProgramVersion") == "1.1R20260928 (Git shallow)", "unqualified source archive version")
        declaration, = root.findall("./Objects/Object")
        owner, = root.findall("./ObjectData/Object")
        dependency, = root.findall("./Objects/ObjectDeps")
        name, class_name, number = (declaration.attrib[key] for key in ("name", "type", "id"))
        require(class_name == ("Part::Feature" if baked else "Part::Box")
                and owner.attrib["name"] == name and dependency.attrib == {"Name": name, "Count": "0"}
                and not len(dependency), "literal owner or dependency state differs")
        rows = properties(owner)
        shape, = (value for value in rows.values() if value.get("type") == "Part::PropertyPartShape")
        part, = shape.findall("./Part")
        member = part.attrib["file"]
        require(shape is rows["Shape"] and sorted(archive.namelist()) == ["Document.xml", member]
                and archive.testzip() is None, "archive has alternate or unowned shape data")
        require(digest(archive.read(member)) == expected["shape_sha256"], "disclosed Shape SHA-256 differs")
        require(not {"Proxy", "ParametricSource"}.intersection(rows) and owner.find(".//Expression") is None,
                "source has a proxy or expression owner")
        driver_names = {key for key, row in rows.items() if row.get("type") == "App::PropertyLength"}
        require(driver_names == (set() if baked else LENGTHS), "native geometric drivers differ")
        driver_lengths = {key: float(rows[key].find("./Float").attrib["value"]) for key in sorted(driver_names)}
        source_placement = rows["Placement"].find("./PropertyPlacement").attrib
        translation = tuple(float(source_placement[f"P{axis}"]) for axis in "xyz")
        rotation = tuple(float(source_placement[f"Q{index}"]) for index in range(4))
        require(rotation == (0., 0., 0., 1.) and (not baked or translation == (0., 0., 0.)),
                "native placement differs from the selected scope")
        if baked:
            require(not owner.findall("./Extensions/Extension") and not any(
                row.get("type", "").startswith(("App::PropertyLink", "App::PropertyXLink", "App::PropertyPythonObject"))
                for row in rows.values()), "baked object has an alternate persistent owner")
        doc_properties = properties(root)
        uid = doc_properties["Uid"].find("./Uuid").attrib["value"]
        label = rows["Label"].find("./String").attrib["value"]
        document_label = doc_properties["Label"].find("./String").attrib["value"]
        material = rows["ShapeMaterial"].find("./PropertyMaterial").attrib["uuid"]
    return {"name": name, "class": class_name, "object_id": number, "label": label,
            "document_label": document_label, "document_uid": uid, "properties": list(rows),
            "shape_member": member, "shape_part_attributes": part.attrib, "shape_material_uuid": material,
            "driver_lengths_mm": driver_lengths, "placement_origin_mm": translation}


def guard_reads(sdk, source):
    safe = (sdk, Path(sys.base_prefix).resolve())
    seen = Counter()

    def audit(event, args):
        if event.startswith("socket.") or event in {"subprocess.Popen", "os.system", "os.posix_spawn", "os.exec"}:
            raise RuntimeError("offline read attempted a process or network operation")
        if event == "import" and str(args[0]).split(".")[0].casefold() in RUNTIME_MODULES:
            raise RuntimeError("offline read attempted a CAD runtime import")
        if event == "open" and not isinstance(args[0], int):
            path = Path(os.fsdecode(args[0])).resolve()
            writes = args[2] & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
            require(not writes and (path == source or any(path.is_relative_to(folder) for folder in safe)),
                    "offline read attempted an undeclared or writable file")
            if path == source:
                seen[path.name] += 1

    sys.addaudithook(audit)
    return seen


def coords(vector):
    return (vector.x, vector.y, vector.z)


def cross(left, right):
    a, b, c = left
    x, y, z = right
    return (b * z - c * y, c * x - a * z, a * y - b * x)


def difference(left, right):
    return tuple(a - b for a, b in zip(left, right, strict=True))


def prove_line_carriers(model, points):
    curves = {curve.id: curve for curve in model.curves}
    require(len(curves) == 12 and {edge.curve_id for edge in model.edges} == set(curves),
            "box does not link all twelve line carriers")
    for edge in model.edges:
        line = curves[edge.curve_id]
        origin, direction = coords(line.origin), coords(line.direction)
        start, end = points[edge.start_vertex_id], points[edge.end_vertex_id]
        axis, = (index for index in range(3) if start[index] != end[index])
        require(tuple(abs(component) for component in direction) == tuple(int(index == axis) for index in range(3)),
                "trimmed edge line direction differs from the computed box axis")
        for parameter, vertex in ((edge.start_parameter, start), (edge.end_parameter, end)):
            actual = tuple(base + parameter * delta for base, delta in zip(origin, direction, strict=True))
            require(dist(actual, vertex) <= 1e-9, "line carrier trim does not end at its actual vertex")


def prove_outward_faces(model, stations, oriented_rings, face_forward):
    faces = {face.id: face for face in model.faces}
    surfaces = {surface.id: surface for surface in model.surfaces}
    loops = {loop.id: loop for loop in model.loops}
    require(len(surfaces) == 6 and {face.surface_id for face in model.faces} == set(surfaces),
            "box does not link all six plane carriers")
    require(all(len(face.loop_ids) == 1 and loops[face.loop_ids[0]].outer for face in model.faces),
            "box face lacks its sole outer loop")
    corners = set(product(*stations))
    sides = set()
    total_area = 0.0
    for use, ring_vectors in zip(model.face_uses, oriented_rings, strict=True):
        ring = tuple(map(coords, ring_vectors))
        require(len(ring) == len(set(ring)) == 4, "oriented face does not bound four unique corners")
        axis, = (index for index in range(3) if len({point[index] for point in ring}) == 1)
        level = ring[0][axis]
        require(set(ring) == {point for point in corners if point[axis] == level},
                "oriented face boundary differs from the computed box plane")
        end = stations[axis].index(level)
        outward = tuple((2 * end - 1) if index == axis else 0 for index in range(3))
        face = faces[use.face_id]
        surface = surfaces[face.surface_id]
        normal, reference = coords(surface.normal), coords(surface.reference_direction)
        actual_normal = tuple(component * (1 if face_forward(face.id) else -1) for component in normal)
        require(actual_normal == outward and abs(coords(surface.origin)[axis] - level) <= 1e-9,
                "effective carrier orientation or plane station differs from the computed box")
        require(abs(reference[axis]) <= 1e-12 and isclose(dist(reference, (0., 0., 0.)), 1., rel_tol=0., abs_tol=1e-12)
                and tuple(surface.attributes["reference_y"]) == cross(normal, reference),
                "source carrier frame is not orthonormal and right-handed")
        area_vector = cross(difference(ring[1], ring[0]), difference(ring[2], ring[1]))
        area = sum(component * expected for component, expected in zip(area_vector, outward, strict=True))
        require(area > 0 and (axis, end) not in sides, "outward coedge cycle or plane incidence differs")
        total_area += area
        sides.add((axis, end))
    require(sides == set(product(range(3), (0, 1))), "box plane set is incomplete")
    return total_area


def boundary_summary(model, design_body):
    from convert.Geometry.Parasolid import BrepTopology
    from convert.adapters.solidworks.Core.Partition.PartMass import PlanarMoments
    from convert.adapters.solidworks.Core.Partition.PartMassRings import ReadMassRings
    from interchange.brep.Curves.BrepCurves import LineCurve
    from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface
    from interchange.geometry.Models.Transform import KTransformIdentity
    from interchange.geometry.Models.VectorSpace import SpaceVector

    body, = model.bodies
    region, = model.regions
    shell, = model.shells
    shell_use, = model.shell_uses
    require(model.validate(frozenset({design_body})) == () and body.design_body_id == design_body
            and body.region_ids == (region.id,) and region.solid and shell.closed and shell_use.shell_id == shell.id
            and body.transform == KTransformIdentity and not (model.pcurves or model.wires),
            "default strict read lost its solid shell or design-body identity")
    require(tuple(len(getattr(model, key)) for key in ("faces", "edges", "vertices", "loops", "coedges"))
            == (6, 12, 8, 6, 24), "box incidence counts differ")
    require(all(type(curve) is LineCurve for curve in model.curves)
            and all(type(surface) is PlaneSurface for surface in model.surfaces), "body has alternate analytic carriers")
    points = {vertex.id: (vertex.point.x, vertex.point.y, vertex.point.z) for vertex in model.vertices}
    stations = tuple(tuple(sorted(set(axis))) for axis in zip(*points.values(), strict=True))
    require(all(len(axis) == 2 for axis in stations) and set(points.values()) == set(product(*stations)),
            "vertices do not form the complete Cartesian box")
    actual = {frozenset((points[edge.start_vertex_id], points[edge.end_vertex_id])) for edge in model.edges}
    expected = {frozenset((a, b)) for a, b in combinations(points.values(), 2)
                if sum(left != right for left, right in zip(a, b, strict=True)) == 1}
    require(actual == expected, "box does not own the twelve adjacent corner edges")
    require(Counter(value.edge_id for value in model.coedges) == Counter({edge.id: 2 for edge in model.edges}),
            "box edge does not have exactly two face trims")
    prove_line_carriers(model, points)
    surface_area = prove_outward_faces(model, stations, ReadMassRings(model), BrepTopology(model).IsFaceForward)
    lengths = [high - low for low, high in stations]
    expected_volume = prod(lengths)
    expected_area = 2 * sum(a * b for a, b in combinations(lengths, 2))
    expected_center = [(low + high) / 2 for low, high in stations]
    anchor = tuple(low for low, _ in stations)
    signed_volume, *first_moments = PlanarMoments(model, SpaceVector(*anchor))
    actual_center = tuple(low + moment / signed_volume for low, moment in zip(anchor, first_moments, strict=True))
    require(isclose(surface_area, expected_area, rel_tol=1e-12) and isclose(signed_volume, expected_volume, rel_tol=1e-12)
            and dist(actual_center, expected_center) <= 1e-9,
            "oriented face integrals differ from computed box volume, area or centre")
    return {"body_id": body.id, "bounds_mm": stations, "volume_mm3": prod(lengths),
            "area_mm2": expected_area, "center_mm": expected_center,
            "outward_planar_faces": 6, "oriented_trim_uses": 24, "linked_line_carriers": 12,
            "shell_use_reversed": shell_use.reversed,
            "reversed_face_uses": sum(value.reversed for value in model.face_uses),
            "tolerances_mm": {key: sorted({entity.tolerance for entity in getattr(model, key)})
                              for key in ("vertices", "edges", "faces")},
            "attribute_entity_counts": {key: sum(bool(entity.attributes) for entity in getattr(model, key))
                                        for key in ("bodies", "faces", "curves", "surfaces")}}


def refusal(operation, *args):
    try:
        operation(*args)
    except ValueError as problem:
        return str(problem)
    raise ValueError("unexpected admission by an existing writer gate")


def read_case(sdk, path, physical, expected):
    sys.path.insert(0, str(sdk))
    reads = guard_reads(sdk, path)
    from convert import open_document
    from convert.adapters.base.WritePolicy import GetDocumentCaps
    from convert.adapters.registry.NativeWrite import CheckNative
    from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxMat import ReadBoxMat
    from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceSchema import KDefaultMat
    from convert.adapters.solidworks.Core.Preparation.Imports.CheckImportGeo import CheckImportGeo
    from convert.adapters.solidworks.Core.Preparation.Imports.PlanImportPart import PlanImportPart
    from convert.adapters.solidworks.Core.Writing.EmitNativeMut import KImportTransfers

    document = open_document(path)
    document.assert_valid()
    feature, = document.feature_timeline
    design, = document.bodies
    config, = document.configurations
    model = document.brep
    body, = model.bodies
    source = document.source
    require(source.sha256 == expected["file_sha256"] and Path(source.path).resolve() == path
            and source.format_id == "freecad.fcstd" and source.application_version == "1.1R20260928 (Git shallow)",
            "strict read detached its source locator or digest")
    owner = feature.definition.object_data
    require(feature.name == physical["label"] and feature.definition.type_id == physical["class"]
            and owner["object_id"] == physical["object_id"] and owner["name"] == physical["name"]
            and not (owner["dependencies"] or feature.input_feature_ids) and owner["property_order"] == physical["properties"],
            "strict feature does not bind the literal archive owner")
    metadata = document.metadata["freecad"]
    doc_props = {row["attributes"]["name"]: row for row in metadata["document_properties"]["children"]
                 if row["tag"] == "Property"}
    require(doc_props["Uid"]["children"][0]["attributes"]["value"] == physical["document_uid"]
            and doc_props["Label"]["children"][0]["attributes"]["value"] == physical["document_label"],
            "strict document metadata differs from its physical identity")
    require(ReadBoxMat(owner["properties"]) == physical["shape_material_uuid"] == KDefaultMat,
            "literal ShapeMaterial does not match the existing measured library default")
    payloads = {payload.role.value: payload for payload in document.brep_payloads}
    require(len(document.brep_payloads) == 3 and set(payloads) == {"brep", "document", "verification"},
            "strict read did not preserve the three actual data owners")
    shape = payloads["brep"]
    require(digest(shape.data) == expected["shape_sha256"] and shape.source_stream == physical["shape_member"]
            and shape.attributes["freecad_part_attributes"] == physical["shape_part_attributes"]
            and shape.attributes["freecad_object"] == physical["name"] and shape.attributes["freecad_object_type"] == physical["class"]
            and shape.attributes["feature_id"] == feature.id and body.attributes["brep_payload_id"] == shape.id
            and body.attributes["feature_id"] == design.final_feature_id == feature.id
            and feature.attributes["brep_payload_ids"] == [shape.id]
            and digest(payloads["document"].data) == expected["file_sha256"]
            and payloads["verification"].data == bytes.fromhex(expected["file_sha256"]),
            "neutral solid has a mismatched feature, Shape, archive or provenance binding")
    baked = expected["standalone_baked"]
    lengths = {parameter.attributes["freecad_path"]: parameter.value.value for parameter in document.parameters
               if parameter.value.kind.value == "length" and parameter.owner_id == feature.id and parameter.value.unit == "mm"}
    require(lengths == physical["driver_lengths_mm"] and (feature.kind.value == "imported") == baked,
            "typed strict history differs from actual geometric ownership")
    if baked:
        require({parameter.attributes["freecad_path"] for parameter in document.parameters} == {"Label", "Label2", "Visibility"}
                and all(parameter.owner_id == feature.id and parameter.expression is None for parameter in document.parameters),
                "standalone object contains alternate parameter semantics")
    bounds = boundary_summary(model, design.id)
    native = refusal(CheckNative, document)
    plan = refusal(PlanImportPart, document, "C:/KitReference/OwnerCheck.SLDPRT")
    geometry = refusal(CheckImportGeo, model)
    missing = sorted(value.value for value in GetDocumentCaps(document) - {row.CapabilityData for row in KImportTransfers})
    return {"strict_read": True, "neutral_sha256": digest(document.to_json(indent=None).encode()),
            "feature_id": feature.id, "feature_kind": feature.kind.value, "design_body_id": design.id,
            "design_body_generated": design.attributes.get("freecad_generated") is True,
            "configuration": config.name, "payload_owners": {key: value.id for key, value in payloads.items()},
            "parameters": [param.attributes["freecad_path"] for param in document.parameters], "library_default_material": True,
            "capabilities_missing_from_bare_recipe": missing, "geometry": bounds,
            "native_refusal": native.replace(str(path), path.name), "document_refusal": plan, "geometry_refusal": geometry,
            "source_reads": reads[path.name], "admission": "unrepresented_source_owners" if baked else "live_parametric_primitive"}


def main(directory):
    directory = directory.resolve(strict=True)
    lock = json.loads(checked_file(directory / "DisclosedSourceLock01.json", LOCK))
    require(lock["passed"] is True and lock["healthy_brackets"] == 4 and lock["native_processes"] == 2
            and lock["baked_sources"] == 2 and lock["live_parametric_controls"] == 1, "disclosed source lock is incomplete")
    root = Path(__file__).resolve().parents[4]
    cases = {}
    with TemporaryDirectory(prefix="kit-baked-fcstd-owner-") as scratch:
        sdk = Path(scratch).resolve() / "src"
        source = check_output(("git", "-C", str(root), "archive", "--format=tar", REVISION, "src"))
        with open_tar(fileobj=BytesIO(source)) as snapshot:
            snapshot.extractall(scratch, filter="data")
        for name, expected in zip(NAMES, lock["inputs"], strict=True):
            path = directory / name
            physical = physical_owner(path, expected)
            result = run((sys.executable, "-I", "-B", __file__, "--worker", str(sdk), str(path)),
                         input=json.dumps((physical, expected)), capture_output=True, text=True, timeout=60)
            require(result.returncode == 0, result.stderr)
            strict = json.loads(result.stdout)
            checked_file(path, expected["file_sha256"])
            cases[name] = {"source_lock": expected, "physical_owners": physical, "strict": strict}
    require(len({row["physical_owners"]["document_uid"] for row in cases.values()}) == 3,
            "disclosed documents share a native identity")
    require(len({row["strict"]["design_body_id"] for row in cases.values()}) == 1,
            "shared local body ID observation differs")
    return {"schema": "kit.freecad.disclosed-baked-owner-audit.v1", "sdk_revision": REVISION,
            "source_lock_sha256": LOCK, "case_count": len(cases), "cases": cases,
            "native_processes_started": 0, "heldout_sources_read": 0, "writer_outputs": 0,
            "whole_source_conversions": 0, "original_fcstd_conversion_credit": 0}


if __name__ == "__main__":
    if sys.argv[1] == "--worker":
        row, expected = json.load(sys.stdin)
        print(json.dumps(read_case(Path(sys.argv[2]), Path(sys.argv[3]), row, expected), sort_keys=True, allow_nan=False))
    else:
        print(json.dumps(main(Path(sys.argv[1])), indent=2, sort_keys=True, allow_nan=False))
