from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from itertools import product
from json import dumps, loads
from pathlib import Path
from struct import calcsize, unpack_from
from subprocess import run
from xml.etree import ElementTree
from zipfile import ZipFile
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
TOOLS = HERE.parents[2]
SW = "src/convert/adapters/solidworks/Core/Preparation/FreecadBox/"
FILES = (
    "src/convert/adapters/freecad/BodyLineage/BoxShapeOwner.py",
    *(SW + value for value in (
        "LowerBoxModel.py",
        "Primitive/CheckStockShape.py",
        "Primitive/PlanFcStock.py",
        "Primitive/PrepFcStock.py",
        "Primitive/ReadStockDims.py",
        "Primitive/ReadStockSource.py",
    )),
)
BASE = "935d9848dab052aff0bc4495faa579e011cc7cba"
INVENTORY = "1de42ebe8bf52b8403de2e6a73fe45b45ac83484a6532230d4b379aff93ca03f"
CASES = {
    "C077-P01": ("85d9b34419fa92b1de954dff2cd8dfe1e0b964e7859b6841e991329d7de931a3",
                 "ec9af7d7345ebc2f23e038c8d1c62cd19a1028975b1367f4dcbb639b4621f8f8"),
    "C114-P01": ("c2e90d3ae6b8d02f11e599b8179643a2f1ccf8d9a3ef1a48e537a118b7372537",
                 "f1473afe52e1ffd7f74a218f915ddfdeeb8c54f9265fe784d52614c4be8487ea"),
    "C151-P01": ("ef5661105657e402988327f6ae87611982d236bf6e5e04eaf9b1606694c2d9d4",
                 "68e0d931c26cbd57c354e5fb9bf79c3870c02c55c38e5e32a57e40c474408342"),
}
OFFSET = "0de6a5bdd0e3c092a8ce12e932a6dd3937a8eaac8b5e7eb1fac37a73151c9c51"
DRIVERS = ("Length", "Width", "Height")
EPOCH = 1790000000
FORMAT = "solidworks.sldprt"
FEATURE = "freecad:feature:Box"

sys.path[:0] = [
    str(ROOT / "src"),
    str(TOOLS),
    str(TOOLS / "attached_top_box_source"),
]

from BoxIncidence import box_incidence
from CheckScopedPlainWriter import WriterAudit, reject
from VerifyLocalSketchExpr import guard_source
from VerifyOriginalFcstdAttachedBox import prewarm
from convert import open_document, write_document
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.registry.RegistryErrors import NotFoundError
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Primitive.CheckStockShape import ReadStockShape
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Primitive.PlanFcStock import PlanFcStock
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Primitive.PrepFcStock import PrepFcStock
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Primitive.ReadStockSource import ReadStockSource
from convert.adapters.solidworks.Archive.Header.ReadFileTable import GetFileRef
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


def digest(data):
    return sha256(data).hexdigest()


def wire(value):
    return (dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def pinned(path, expected):
    raw = path.read_bytes()
    assert digest(raw) == expected, "disclosed source identity changed"
    return raw


def source_owners(raw, name, case):
    with ZipFile(BytesIO(raw)) as bundle:
        archive = ElementTree.fromstring(bundle.read("Document.xml"))
        objects = {row.attrib["name"]: row for row in archive.findall("./Objects/Object")}
        data = {row.attrib["name"]: row for row in archive.findall("./ObjectData/Object")}
        assert objects[name].attrib["type"] == "Part::Box"
        fields = {row.attrib["name"]: row for row in data[name].findall("./Properties/Property")}
        shape = fields["Shape"][0].attrib["file"]
        result = {
            "release": archive.attrib["ProgramVersion"],
            "native_object_id": objects[name].attrib["id"],
            "source_alias": fields["Label"][0].attrib["value"],
            "size_mm": [float(fields[key][0].attrib["value"]) for key in DRIVERS],
            "placement_mm": [float(fields["Placement"][0].attrib[key]) for key in ("Px", "Py", "Pz")],
            "shape_sha256": digest(bundle.read(shape)),
        }
        if case == "C114-P01":
            edges = data["Chamfer"].find("./Properties/Property[@name='Edges']/*")
            payload = bundle.read(edges.attrib["file"])
            count, = unpack_from("<I", payload)
            rows = [unpack_from("<idd", payload, 4 + calcsize("<idd") * index)
                    for index in range(count)]
            assert count == 12 and len(payload) == 4 + 12 * calcsize("<idd")
            assert sorted(rows) == [(index, 1.0, 1.0) for index in range(1, 13)]
            assert data["Chamfer"].find("./Properties/Property[@name='Base']/Link").attrib["value"] == name
            result["independent_untranslated_history"] = {"native": "Part::Chamfer", "edge_count": count}
        elif case == "C077-P01":
            links = [data["Cut"].find(f"./Properties/Property[@name='{key}']/Link").attrib["value"]
                     for key in ("Base", "Tool")]
            assert links == [name, "Cylinder"]
            placement = data["Cylinder"].find("./Properties/Property[@name='Placement']/*")
            tool = [float(placement.attrib[key]) for key in ("Px", "Py", "Pz")]
            height = float(data["Cylinder"].find("./Properties/Property[@name='Height']/*").attrib["value"])
            assert tool == [5.0, 5.0, 5.0] and height == 10.0
            result["independent_untranslated_history"] = {
                "native": "Part::Cut", "base": links[0], "tool": links[1],
                "tool_origin_mm": tool, "tool_height_mm": height,
            }
        return result


def refuse_public(document, locator, reason_type=NotFoundError, reason="does not support the destination"):
    target = BytesIO(b"unmodified owner")
    target.seek(2)
    values = {"require_native_transfers": True, "final_destination": locator}
    outcomes = {
        "registry": reject(
            lambda: write_document(document, target, destination_format=FORMAT,
                                   allow_carrier=False, values=values), reason_type, reason),
        "adapter": reject(
            lambda: SldprtAdapter().write(document, target, WriteOptions(values=values)),
            reason_type, reason),
    }
    assert target.getvalue() == b"unmodified owner" and target.tell() == 2
    return outcomes


def target_evidence(candidate, locator, source, selected):
    assert candidate.BytesValue
    full = open_document(candidate.BytesValue, source_format=FORMAT, strict=True)
    design = open_document(candidate.BytesValue, source_format=FORMAT, strict=True,
                           include_brep=False)
    boss, = (row for row in full.feature_timeline if row.name == source["source_alias"])
    sketch, = full.sketches
    sketch_feature, = (row for row in full.feature_timeline if row.name == sketch.name)
    body, = full.bodies
    assert boss.kind == "extrusion" and boss.definition.length.value == source["size_mm"][2]
    assert boss.operation == "create" and boss.sketch_id == sketch.id
    assert body.final_feature_id == boss.id and body.name == source["source_alias"]
    assert full.configurations[0].name == design.configurations[0].name == selected.configurations[0].name
    assert full.configurations[0].active and design.configurations[0].active
    design_boss, = (row for row in design.feature_timeline if row.id == boss.id)
    assert design_boss.operation == "join"
    assert tuple(replace(row, operation=boss.operation) if row.id == boss.id else row
                 for row in design.feature_timeline) == full.feature_timeline
    assert design.parameters == full.parameters
    assert design.brep is None and not design.brep_payloads and not full.brep_payloads
    assert design.bodies[0].final_feature_id == body.final_feature_id
    topology = body.topology
    assert (topology.solid_count, topology.shell_count, topology.face_count,
            topology.edge_count, topology.vertex_count) == (1, 1, 6, 12, 8)
    x, y, z = source["size_mm"]
    assert topology.volume == x * y * z
    assert topology.surface_area == 2 * (x * y + x * z + y * z)
    assert full.brep is not None
    corners = tuple(product((0.0, x), (0.0, y), (0.0, z)))
    _, incidence = box_incidence(full.brep, corners, body.id)
    indexed = {row.name.rsplit(".", 1)[1]: row for row in full.parameters}
    drivers = {}
    for key, amount, owner in zip(DRIVERS, source["size_mm"],
                                  (sketch_feature, sketch_feature, boss), strict=True):
        parameter = indexed[key]
        assert parameter.name == source["source_alias"] + "." + key
        assert parameter.role == "driving" and parameter.value.kind == "length"
        assert parameter.owner_id == owner.id and parameter.value.unit == "mm"
        assert parameter.value.value == amount and parameter.expression is None
        drivers[key] = {"name": parameter.name, "owner": owner.kind, "mm": amount}
    assert len(full.parameters) == len(indexed) == 3
    archive = SldprtArchive.from_bytes(candidate.BytesValue)
    assert archive.streams == candidate.StreamsValue
    link = ReadNativeLink(archive, full.configurations[0].attributes["native_configuration_id"])
    features = IndexFeatures(link)
    classes = [row.ClassValue.NameValue for row in features.values()]
    assert classes.count("moExtrusion_c") == 1 and classes.count("moProfileFeature_c") == 1
    file = GetFileRef(link.ConfigValue.HeaderValue.FieldsValue["f38"])
    assert file.PathValue == locator
    return {
        "sha256": digest(candidate.BytesValue), "bytes": len(candidate.BytesValue),
        "streams": {key: {"bytes": len(value), "sha256": digest(value)}
                    for key, value in archive.streams.items()},
        "linked_rows": len(features), "drivers": drivers,
        "body_alias_full_read": body.name, "body_alias_design_only": design.bodies[0].name,
        "creator_operation_full_read": boss.operation, "creator_operation_design_only": design_boss.operation,
        "typed_incidence": incidence,
        "volume_mm3": topology.volume, "area_mm2": topology.surface_area,
        "center_mm_from_corners": [sum(point[index] for point in corners) / len(corners)
                                   for index in range(3)],
    }


def verified_candidate(document, raw, request, source):
    case = request["case"]
    locator = f"C:\\KitSdkCandidates\\{case[:4]}-Stock.SLDPRT"
    if case == "offset":
        assert source["placement_mm"] == [4.25, 6.125, -2.25]
        assert source["size_mm"] == [17.375, 13.625, 9.75]
        feature = "freecad:feature:Specimen"
        return {
            "refusal": reject(lambda: PrepFcStock(document, feature, locator, EPOCH),
                              ValueError, "alternate attachment or placement"),
            "public_refusals": refuse_public(
                document, locator, ValueError, "native-only feature definitions cannot be exported"),
        }
    assert source["placement_mm"] == [0, 0, 0]
    selected = PlanFcStock(document, FEATURE, case[:4] + "-Stock")
    assert selected.source is document.source and selected.configurations == document.configurations
    assert selected.brep is None and not selected.brep_payloads
    original_params = {row.id: row for row in document.parameters}
    for row in selected.parameters:
        original = original_params[row.id]
        assert row.name == original.name and row.value == original.value
    assert selected.feature_timeline[0].id == FEATURE and selected.bodies[0].id == FEATURE + ":stock"
    owner, item, _ = ReadStockSource(document, FEATURE)
    original = ReadStockShape(document, owner, item, FEATURE, tuple(source["size_mm"]))
    corners = tuple(product(*((0.0, value) for value in source["size_mm"])))
    _, shape = box_incidence(original, corners, FEATURE)
    candidate = PrepFcStock(document, FEATURE, locator, EPOCH)
    actual = target_evidence(candidate, locator, source, selected)
    assert actual["typed_incidence"] == shape
    assert actual["sha256"] == CASES[case][1]
    owned = selected.parameters[0].id
    wrong_parameter = replace(document, parameters=tuple(
        replace(row, name=row.name + " altered") if row.id == owned else row
        for row in document.parameters))
    wrong_shape = replace(document, brep_payloads=tuple(
        row for row in document.brep_payloads if row.sha256 != source["shape_sha256"]))
    refusals = {
        "renamed_source_parameter": reject(lambda: PrepFcStock(wrong_parameter, FEATURE, locator, EPOCH),
                                          ValueError, "parameters disagree"),
        "missing_source_shape": reject(lambda: PrepFcStock(wrong_shape, FEATURE, locator, EPOCH),
                                       ValueError, "ambiguous or empty shape payload"),
    }
    if case == "C151-P01":
        other = source_owners(raw, "Box001", "offset-owner")
        assert other["placement_mm"] == [181.8, 0, 0] and other["size_mm"] == [160.0, 400.0, 5.0]
        assert other["source_alias"] == "160x400x006"
        refusals["other_actual_part_box"] = reject(
            lambda: PrepFcStock(document, "freecad:feature:Box001", locator, EPOCH),
            ValueError, "alternate attachment or placement",
        )
        refusals["other_actual_owner"] = other
    else:
        name = "Chamfer" if case == "C114-P01" else "Cut"
        refusals["actual_consuming_feature"] = reject(
            lambda: PrepFcStock(document, "freecad:feature:" + name, locator, EPOCH),
            ValueError, "actual independent Part::Box",
        )
    return {
        "candidate": actual, "source_geometry_matches_complete_corner_incidence": True,
        "source_parameter_ids": [row.id for row in selected.parameters],
        "intact_public_refusals": refuse_public(
            document, locator, ValueError, "native-only feature definitions cannot be exported"),
        "projected_public_refusals": refuse_public(selected, locator),
        "refusals": refusals,
    }


def worker(request):
    case = request["case"]
    path = Path(request["path"]).resolve(strict=True)
    compact = "".join(character for character in str(path).casefold() if character.isalnum())
    assert path.suffix.casefold() == ".fcstd"
    assert not any(marker in compact for marker in ("holdout", "heldout", "sealed"))
    source_hash = OFFSET if case == "offset" else CASES[case][0]
    raw = pinned(path, source_hash)
    prewarm()
    reads, denied = guard_source(path, ROOT / "src")
    document = open_document(path, source_format="freecad.fcstd", strict=True)
    assert reads and not denied and document.source.sha256 == source_hash
    read_count = len(reads)
    source = source_owners(raw, "Specimen" if case == "offset" else "Box", case)
    original = document.to_json(indent=None)
    audit = WriterAudit(ROOT / "src", Path("Unused.SLDPRT"))
    sys.addaudithook(audit.observe)
    audit.phase = "prepare"
    try:
        result = verified_candidate(document, raw, request, source)
        assert document.to_json(indent=None) == original
    finally:
        audit.phase = "done"
    assert not audit.denied and not audit.target_opens and not denied and len(reads) == read_count
    assert pinned(path, source_hash) == raw
    return {
        "source_sha256": source_hash, "source": source, "result": result,
        "source_file_and_neutral_unchanged": True, "runtime_input_file_reads": 0,
    }


def main(inventory, offset):
    rows = loads(pinned(inventory, INVENTORY))["files"]
    requests = []
    for case, (source_pin, _) in CASES.items():
        row, = (value for value in rows if value["case_id"] == case)
        assert row["sha256"] == source_pin
        requests.append({"case": case, "path": row["source_path"]})
    requests.append({"case": "offset", "path": str(offset)})
    results = {}
    for request in requests:
        children = tuple(run((sys.executable, "-I", "-B", str(HERE), "--worker"),
                             input=wire(request), capture_output=True, timeout=120) for _ in range(2))
        for child in children:
            if child.returncode or child.stderr:
                sys.stderr.buffer.write(child.stderr)
                raise ValueError("guarded source stock worker failed")
        assert children[0].stdout == children[1].stdout
        results[request["case"]] = loads(children[0].stdout)
    stream = "Contents/Config-0-ResolvedFeatures"
    changed_lengths = {result["result"]["candidate"]["streams"][stream]["bytes"]
                       for key, result in results.items() if key != "offset"}
    assert len(changed_lengths) >= 2
    return {
        "schema": "kit.sw2026.freecad-source-stock.v1", "base": BASE,
        "source_manifest_sha256": INVENTORY, "creation_epoch": EPOCH,
        "code_sha256": {str(path.relative_to(ROOT)): digest(path.read_bytes())
                        for path in (*(ROOT / entry for entry in FILES), HERE)},
        "cases": results, "fresh_workers": 2 * len(requests),
        "resolved_stream_distinct_lengths": sorted(changed_lengths),
        "whole_source_qualified": False, "native_processes": 0, "corpus_credit": 0,
    }


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--offset-control", type=Path)
    parser.add_argument("--worker", action="store_true")
    arguments = parser.parse_args()
    if not arguments.worker and (arguments.inventory is None or arguments.offset_control is None):
        parser.error("Both disclosed source pins are required.")
    sys.stdout.buffer.write(wire(worker(loads(sys.stdin.buffer.read())) if arguments.worker
                                 else main(arguments.inventory, arguments.offset_control)))
