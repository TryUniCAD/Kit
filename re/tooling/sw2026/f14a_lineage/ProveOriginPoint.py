from argparse import ArgumentParser
from dataclasses import replace
from io import BytesIO
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory
from xml.etree.ElementTree import fromstring
from zipfile import ZipFile
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ProveOriginAxes import (
    CASES, MANIFEST, ROOT, SW, digest, lookup, no_runtime_io, pinned, prewarm, refused,
    refusal, replace_owner, source_object, wire, with_value, writer_boundary, xyz,
)
from FixedPointRecord import DATA, FEATURE, VIRTUAL_SLOTS, decode, encode, fixed_point
from PinPointLibrary import SHARED_DISPATCH, audit
from convert import open_document
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Core.Preparation.FreecadBox.PlanOriginBox import PlanOriginBox
from convert.adapters.solidworks.Core.Preparation.FreecadBox.PrepOrigAxes import PrepOrigAxes
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxDatums import ReadBoxPoint

BASE = "ed3243fa745d6ffd8379126db483179a547eb4cd"
SRC_TREE = "ab7d5f9a2aff0a4967368cc94d522a28d11f4bc1"
AXIS_RECEIPT = ROOT / "re/solidworks/measurements/2026/SdkFreecadOriginBoxAxes01.json"
ORIGIN_PLAN = ROOT / "re/solidworks/measurements/2026/SdkFreecadF14aOriginPlan01.json"
SOURCE_FILES = (
    "Core/Preparation/FreecadBox/PlanOriginBox.py",
    "Core/Preparation/FreecadBox/PrepOrigAxes.py",
    "Core/Preparation/FreecadBox/Source/BoxDatums.py",
    "Core/Preparation/FreecadBox/Source/ReadBoxDatums.py",
)


def exact_source_point(raw, point, has_point):
    with ZipFile(BytesIO(raw)) as archive:
        assert "GuiDocument.xml" not in archive.namelist()
        root = fromstring(archive.read("Document.xml"))
    body_origin, = root.findall("./ObjectData/Object[@name='Body']/Properties/Property[@name='Origin']/Link")
    group, = root.findall("./Objects/Object[@name='Origin']")
    assert body_origin.attrib == {"value": group.attrib["name"]} and group.attrib["type"] == "App::Origin"
    links, = root.findall("./ObjectData/Object[@name='Origin']/Properties/Property[@name='OriginFeatures']/LinkList")
    rows = root.findall("./Objects/Object[@type='App::Point']")
    assert len(rows) == int(has_point)
    if not has_point:
        assert point is None and all(link.get("value") != "Origin001" for link in links)
        return None
    row, = rows
    name = row.attrib["name"]
    assert name == point.ObjectName == "Origin001" and row.attrib["id"] == point.RecordId
    assert group.attrib["id"] == point.OriginId and sum(link.get("value") == name for link in links) == 1
    values, = root.findall(f"./ObjectData/Object[@name='{name}']/Properties")
    place, = values.findall("./Property[@name='Placement']/PropertyPlacement")
    label, = values.findall("./Property[@name='Label']/String")
    role, = values.findall("./Property[@name='Role']/String")
    shown, = values.findall("./Property[@name='Visibility']/Bool")
    source_xyz = tuple(float(place.attrib[key]) for key in ("Px", "Py", "Pz"))
    assert source_xyz == xyz(point.PointMm) == (0.0, 0.0, 0.0)
    assert point.LabelValue == label.attrib["value"] and role.attrib == {"value": "Origin"}
    assert point.RecordShown and shown.attrib == {"value": "true"}
    return {
        "group_id": point.OriginId, "point_id": point.RecordId, "record_name": name,
        "name": point.LabelValue, "role": role.attrib["value"], "coordinates_mm": source_xyz,
        "model_visibility": point.RecordShown, "stored_gui_document": False,
    }


def source_faults(document, point):
    row = source_object(document, point.ObjectName)
    changed = replace_owner(document, with_value(row, "Label", "Unbound point"))
    return {
        "unbound_label": refusal(lambda: PlanOriginBox(changed), "FreeCAD origin datum owners disagree with the source archive"),
        "wrong_native_kind": refusal(lambda: ReadBoxPoint({**row, "type_id": "App::Line"}, point.OriginId),
                                     "FreeCAD origin datum has an unrepresented owner or property"),
        "nonprincipal_location": refusal(lambda: ReadBoxPoint(with_value(row, "Placement", "2.0", key="Px"), point.OriginId),
                                         "FreeCAD origin point requires its fixed visible principal placement"),
        "wrong_model_visibility": refusal(lambda: ReadBoxPoint(with_value(row, "Visibility", "false"), point.OriginId),
                                          "FreeCAD origin point requires its fixed visible principal placement"),
    }


def entry_signature(row):
    value = row.EntryValue
    cls = value.ClassValue if isinstance(value, ArchiveNode) else value
    return row.IndexValue, isinstance(value, ArchiveNode), cls.NameValue, cls.SchemaValue


def point_capsule(stock, label, position_mm, epoch):
    data = fixed_point(stock, label, position_mm, epoch)
    blob, emitted = encode(stock, data)
    result, consumed = decode(stock, blob)
    seed = stock.ResolvedValue.MapValue
    assert emitted.EntriesValue[:len(seed.EntriesValue)] == consumed.EntriesValue[:len(seed.EntriesValue)] == seed.EntriesValue
    slots = tuple(entry_signature(row) for row in consumed.EntriesValue[len(seed.EntriesValue):])
    assert slots == tuple(entry_signature(row) for row in emitted.EntriesValue[len(seed.EntriesValue):])
    assert emitted.CounterValue == consumed.CounterValue == seed.CounterValue + len(slots)
    fields = result.FieldsValue
    assert result.ClassValue == FEATURE and fields["f700"].ClassValue == DATA
    assert fields["owner"] is stock.SystemValue.RootValue
    assert ReadNodeName(result) == label and result.IndexValue == slots[1][0]
    assert fields["f08"] == stock.TopHeader.FieldsValue["f08"]
    assert tuple(fields["f6c0"][name] for name in "xyz") == tuple(component * 0.001 for component in position_mm)
    assert encode(stock, result)[0] == blob
    assert fields["f08"] not in {node.FieldsValue.get("f08") for node in stock.ResolvedValue.RootsValue if node is not None}
    prior_id = stock.ResolvedValue.RootsValue[-1].FieldsValue["f08"]

    def altered(field, value):
        return encode(stock, ArchiveNode(FEATURE, {**data.FieldsValue, field: value}))[0]
    return {
        "name": label, "feature_id": fields["f08"], "xyz_m": fields["f6c0"],
        "map_before": seed.CounterValue, "map_after": consumed.CounterValue, "added_slots": slots,
        "bytes": len(blob), "sha256": digest(blob), "typed_replay": True,
        "refusals": {
            "unbound_owner": refusal(lambda: altered("owner", data), "fixed point requires its actual part owner"),
            "duplicate_persistent_id": refusal(lambda: decode(stock, altered("f08", prior_id)), "fixed reference point has another actual graph owner or mode"),
            "missing_data": refusal(lambda: decode(stock, altered("f700", None)), "fixed reference point has another actual graph owner or mode"),
            "alternate_inherited_mode": refusal(lambda: decode(stock, altered("f6dc", 5)), "fixed reference point has another actual graph owner or mode"),
            "appended": refusal(lambda: decode(stock, blob + b"\x00"), "fixed reference point bytes have a different graph boundary"),
            "truncated": refused(lambda: decode(stock, blob[:-1]), ValueError, "field f708 at", ROOT),
            "nonfinite": refusal(lambda: fixed_point(stock, label, (float("inf"), 0, 0), epoch), "fixed reference point requires a named finite coordinate"),
        },
    }


def worker(request):
    path = Path(request["path"])
    raw = pinned(path, request["sha256"])
    assert len(raw) == request["bytes"]
    document = open_document(path, strict=True, include_brep=True, include_tessellation=True)
    assert document.source.sha256 == request["sha256"]
    before = document.to_dict()
    prewarm()
    lookup("utf-8-sig")
    has_point = request["case"] == "recipe-1.1.4-F14a"
    with no_runtime_io():
        plan = PlanOriginBox(document)
        point = plan.SourceDatums.PointValue
        owner = exact_source_point(raw, point, has_point)
        portable = type(document).from_json(document.to_json(indent=None))
        assert PlanOriginBox(portable).SourceDatums == plan.SourceDatums
        locator = request["locator"]
        stock = PrepOrigAxes(document, locator)
        assert digest(stock.BytesValue) == request["prior_axes_sha256"]
        assert PrepOrigAxes(portable, locator).BytesValue == stock.BytesValue
        epoch = plan.PartSource.CreationEpoch
        name, xyz_mm = (point.LabelValue, xyz(point.PointMm)) if has_point else ("Displaced datum", (-12.5, 28.0, 7.75))
        research_point = point_capsule(stock, name, xyz_mm, epoch)
        source_negatives = source_faults(document, point) if has_point else {}
    with TemporaryDirectory(prefix="KitOriginPointDenied.") as directory:
        boundary = writer_boundary(document, path, Path(directory))
    assert document.to_dict() == before and pinned(path, request["sha256"]) == raw
    return {
        "source_sha256": request["sha256"], "actual_owner": owner,
        "neutral_json_datums_exact": True, "stock_with_axes_sha256": digest(stock.BytesValue),
        "stock_body": plan.PartSource.SourceBodyName,
        "stock_axes": [axis.LabelValue for axis in plan.SourceDatums.AxisValue.AxisValues],
        "stock_drivers": [row.name for row in plan.SourceDrivers], "stock_geometry_roles": len(plan.SourceLineage.Elements),
        "research_record": research_point, "source_negatives": source_negatives,
        "no_publication": boundary, "runtime_file_reads": 0, "model_and_source_unchanged": True,
    }


def main(manifest, library):
    inventory = json.loads(pinned(manifest, MANIFEST))
    assert inventory["heldout_inputs"] == 0 and not inventory["original_corpus_membership_verified"]
    axes_raw, plan_raw = AXIS_RECEIPT.read_bytes(), ORIGIN_PLAN.read_bytes()
    axes, origin = json.loads(axes_raw), json.loads(plan_raw)
    assert axes["input_manifest_sha256"] == MANIFEST
    assert tuple(SHARED_DISPATCH) == VIRTUAL_SLOTS
    library_report = audit(library)
    reports = {}
    for case in ("recipe-1.0.2-F14a", "recipe-1.1.4-F14a"):
        entry, = (row for row in inventory["inputs"] if row["case"] == case)
        assert entry["sha256"] == CASES[case][1]
        request = entry | {
            "locator": origin["cases"][case]["original_logical_destination"],
            "prior_axes_sha256": axes["reports"][case]["model_only_build"]["sha256"],
        }
        workers = []
        for _ in range(2):
            task = run([sys.executable, "-I", "-B", str(Path(__file__).resolve()), "--worker"],
                       input=wire(request), capture_output=True, timeout=90)
            assert task.returncode == 0 and not task.stderr, task.stderr.decode(errors="replace")
            workers.append(json.loads(task.stdout))
        assert workers[0] == workers[1]
        reports[case] = workers[0]
    return {
        "schema": "kit.sw2026.freecad-origin-point.v1", "base": BASE, "base_src_tree": SRC_TREE,
        "source_manifest_sha256": MANIFEST, "prior_axes_receipt_sha256": digest(axes_raw),
        "prior_origin_plan_sha256": digest(plan_raw), "exact_build_static_receipt": library_report,
        "sdk_source_sha256": {path: digest((SW / path).read_bytes()) for path in SOURCE_FILES},
        "tool_source_sha256": {name: digest(Path(__file__).with_name(name).read_bytes()) for name in
                               ("FixedPointRecord.py", "PinPointLibrary.py", "ProveOriginAxes.py", "ProveOriginPoint.py")},
        "reports": reports, "fresh_workers": 4, "native_processes": 0, "heldout_cases": 0,
        "native_sldprt_point_candidate": False, "new_native_acceptance": 0, "corpus_credit": 0,
    }


if __name__ == "__main__":
    if sys.argv[1:] == ["--worker"]:
        result = worker(json.load(sys.stdin))
    else:
        parser = ArgumentParser()
        parser.add_argument("disclosed_manifest", type=Path)
        parser.add_argument("licensed_sldmodu", type=Path)
        arguments = parser.parse_args()
        result = main(arguments.disclosed_manifest, arguments.licensed_sldmodu)
    print(json.dumps(result, sort_keys=True, indent=2))
