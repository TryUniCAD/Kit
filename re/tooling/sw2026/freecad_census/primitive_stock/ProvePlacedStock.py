from argparse import ArgumentParser
from base64 import b64decode, b64encode
from collections import Counter
from itertools import product
from json import loads
from math import cos, dist, hypot, isclose, sin
from pathlib import Path
from subprocess import run
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from ProveSourceStock import (
    CASES, EPOCH, FORMAT, INVENTORY, OFFSET, ROOT, WriterAudit,
    box_incidence, digest, guard_source, open_document, pinned, prewarm,
    refuse_public, reject, source_owners, wire,
)
from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from convert.Geometry.Opencascade import DecodeAsciiBrep
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Construction.Geometry.FrameXform import FrameXform
from convert.adapters.solidworks.Archive.Header.ReadFileTable import GetFileRef
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Primitive.CheckStockShape import ReadStockShape
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Primitive.PlanFcStock import PlanFcStock
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Primitive.PrepFcStock import PrepFcStock
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Primitive.ReadStockSource import ReadStockSource
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismAtom import CheckPrismAtom
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismEnd import CheckPrismEnd
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismMgr import CheckPrismMgr
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismPlane import CheckPrismPlane
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismProf import CheckPrismProf
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismRels import CheckPrismRels
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismRoot import CheckPrismRoot
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismRoots import CheckPrismRoots
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Checks.CheckBossState import CheckBossState
from convert.adapters.solidworks.Core.TypedResolved.Geometry.IsCacheAbsent import IsCacheAbsent
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismClasses import KPrismClasses
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PrismNodes import PrismNodes
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import ReadPrismFrame
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckDimGraph import CheckDimGraph
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckDimGroups import CheckDimGroups
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineDims import LineDims
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadAxisDim import ReadAxisDim
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimRows import ReadDimRows
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadLineDriver import ReadLineDriver
from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLineLoop import ReadLineLoop
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.TypedResolved.OffsetPlanes.ReadOffBase import ReadOffLink
from convert.adapters.solidworks.Core.TypedResolved.OffsetPlanes.ReadOffDatum import ReadOffDatum
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.geometry.Models.VectorSpace import SpaceVector

BASE = "2e3c2ab7c83ae5f6632dbc0bf64482f7546d8bab"
SOURCES = {
    "C151-P01": ("Box001", "C151-TranslatedStock", CASES["C151-P01"][0]),
    "C057-P01": ("Box001", "C057-RotatedStock", "6f821c04ddd34092779e6781288cef62436f108dee5ff948117d35820d3d9c87"),
    "standalone": ("Specimen", "DisclosedLiveBox", OFFSET),
}
STOCK = "src/convert/adapters/solidworks/Core/Preparation/FreecadBox/Primitive/"
BUILDS = "src/convert/adapters/solidworks/Archive/Construction/"
CODE = (
    *(STOCK + name + ".py" for name in (
        "BindStockFix", "BuildPlacedBox", "CheckStockShape", "PlanFcStock",
        "PrepFcStock", "ReadStockDims", "ReadStockPlace",
    )),
    *(BUILDS + name + ".py" for name in (
        "OffsetPlane/BeginOffProf", "OffsetPlane/CheckOffProf", "OffsetPlane/CheckOffRadial",
        "OffsetPlane/MakeOffCircMut", "OffsetPlane/MakeOffPolyMut",
        "SketchDimensions/MakeRectDimsMut", "SketchDimensions/ReadRectDrivers",
    )),
)


def point(value):
    return value.x, value.y, value.z


def fixed_profile(profile, link):
    sketch = RequireNative(profile.FieldsValue["pd_f80"], "sgSketch")
    fields = NativeRecord(sketch.FieldsValue["dims"])
    CheckDimGroups(fields)
    *axis, fixed = ReadDimRows(fields, "nlog1", "log_g1")
    assert len(axis) == 4
    owned = NativeRecord(fixed["d"])
    handle = RequireNative(owned["h1"], "sgPointHandle")
    assert handle.FieldsValue == {"idx": 0, "f1c": -1, "f08": 0}
    assert dict(owned) == {
        "refcount": 0, "f28": None, "f48": None, "f50": -1, "f30": 0, "f54": 0,
        "f5c": 0, "f60": None, "f68": 0, "has_f78": 0, "f80": 17, "f90": 2,
        "f94": 0, "f98": 0, "fa0": 65534, "fa4": 0, "h1": handle,
    }
    rows = ReadDimRows(fields, "ng2", "val_g2")
    displays = RequireNative(fields["f118"], "suObList").FieldsValue
    assert len(rows) == len(NativeRows(displays["items"])) == displays["n"] == 2
    drivers = tuple(ReadLineDriver(row, index, RequireNative(display["o"], "moDisplayDistanceDim_c"),
                                   sketch, link)
                    for index, (row, display) in enumerate(zip(rows, displays["items"], strict=True)))
    assert len({driver.ParamValue for driver in drivers}) == 2
    assert all(driver.NodeValue.FieldsValue["f28"] is driver.ParamValue for driver in drivers)
    relations = tuple(ReadAxisDim(row, index, sketch, link) for index, row in enumerate(axis))
    refs = Counter(("point", index) for driver in drivers for index in driver.PointValues)
    refs.update(("line", row.LineValue) for row in relations)
    refs["point", 0] += 1
    dims = LineDims(drivers, relations, dict(refs))
    loop = ReadLineLoop(sketch, link, dims)
    CheckDimGraph(loop, dims)
    return loop, drivers, handle


def read_frame(profile, link, features, offset):
    root = link.ConfigValue.RootValue
    if offset is None:
        return ReadPrismFrame(profile, root, features), None
    base, frame, depth, reverse = ReadOffDatum(link, offset, features)
    assert ReadNodeName(base) == "Front Plane"
    assert profile.FieldsValue["pd_ff0"] == FrameXform(frame)
    assert NativeNodeId(base) < NativeNodeId(offset) < NativeNodeId(profile)
    ReadOffLink(RequireNative(profile.FieldsValue["pd_f78"], "moCompRefPlane_c"),
                root, NativeNodeId(offset), 0)
    return Transform(
        SpaceVector(*(value * 1000.0 for value in frame.OriginValue)),
        SpaceVector(*frame.AxisU), SpaceVector(*frame.AxisV), SpaceVector(*frame.NormalValue),
    ), {
        "read_owner": ReadNodeName(offset),
        "distance_mm": depth.DepthValue.value_mm,
        "reversed": reverse,
        "live_parameter": depth.DepthValue.name,
    }


def check_tool(stock, size, location, candidate, locator, alias, design_id):
    archive = SldprtArchive.from_bytes(candidate.BytesValue)
    assert archive.streams == candidate.StreamsValue
    assert len(archive.streams) == 10 and IsCacheAbsent(archive)
    link = ReadNativeLink(archive, 0)
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), 19000)
    features = IndexFeatures(link)
    profile, = (value for value in features.values() if value.ClassValue.NameValue == "moProfileFeature_c")
    boss, = (value for value in features.values() if value.ClassValue.NameValue == "moExtrusion_c")
    datums = tuple(value for value in features.values()
                   if value.ClassValue.NameValue == "moRefPlane_c"
                   and value.FieldsValue["f6f8"].ClassValue.NameValue == "moFaceRefPlnData_c")
    assert ReadNodeName(boss) == alias and len(datums) == int(location[2] != 0)
    offset = datums[0] if datums else None
    for report in (link.ConfigValue.ReportValue, link.ResolvedValue.ReportValue, manager.ReportValue):
        assert report["completed"] and not (report["missing_schemas"] or report["provisional_schemas"])
    CheckPrismRoots(features, PrismNodes(link, manager, AllowedClasses=KPrismClasses | {"moFaceRefPlnData_c"}),
                    HasOffset=bool(datums))
    CheckPrismRoot(link.ConfigValue.RootValue, NullRect=bool(datums))
    CheckPrismRels(link.ConfigValue.RootValue)
    CheckPrismMgr(manager)
    CheckPrismPlane({key: value for key, value in features.items() if value is not offset},
                    link.ConfigValue.RootValue, FrontOnly=not datums)
    CheckPrismProf(profile)
    frame, datum = read_frame(profile, link, features, offset)
    assert (frame.origin.x, frame.origin.y) == (0, 0)
    assert isclose(frame.origin.z, location[2], rel_tol=0, abs_tol=1e-10)
    loop, drivers, handle = fixed_profile(profile, link)
    assert all(isclose(a, b, rel_tol=0, abs_tol=1e-10)
               for a, b in zip(loop.PointsValue[0].PositionValue, location[:2], strict=True))
    owner = ReadExtrude(link, boss, features)
    CheckPrismAtom(boss)
    CheckBossState(boss)
    CheckPrismEnd(owner)
    assert owner.ProfileValue is profile and owner.ParentsValue == (profile,)
    assert owner.ModeValue == "blind" and not owner.IsReversed
    depth = owner.RequireDepth().DepthValue
    names = [value.NameValue for value in drivers] + [depth.name]
    amounts = [value.MetresValue * 1000 for value in drivers] + [depth.value_mm]
    assert names == [alias + "." + role for role in ("Length", "Width", "Height")]
    assert all(isclose(first, second, rel_tol=1e-12, abs_tol=0)
               for first, second in zip(amounts, size, strict=True))
    model, volume, area, bounds = BuildPrism(
        design_id, frame, tuple(
            LineGeometry(PlaneVector(*loop.PointsValue[segment.StartValue].PositionValue),
                         PlaneVector(*loop.PointsValue[segment.EndValue].PositionValue))
            for segment in (loop.LinesValue[index] for index in loop.OrderValue)
        ), 0, depth.value_mm,
    )
    limits = tuple(tuple((low, low + length)) for low, length in zip(location, size, strict=True))
    corners = tuple(product(*limits))
    _, expected = box_incidence(stock, corners, stock.bodies[0].design_body_id)
    _, observed = box_incidence(model, corners, design_id)
    assert expected == observed
    x, y, z = size
    assert isclose(volume, x * y * z, rel_tol=1e-12)
    assert isclose(area, 2 * (x*y + x*z + y*z), rel_tol=1e-12)
    file = GetFileRef(link.ConfigValue.HeaderValue.FieldsValue["f38"])
    assert file.PathValue == locator
    assert handle.FieldsValue["idx"] == 0
    handle.FieldsValue["idx"] = 1
    try:
        try:
            fixed_profile(profile, link)
        except AssertionError:
            wrong_corner_refused = True
        else:
            raise ValueError("wrong attached stock corner qualified")
    finally:
        handle.FieldsValue["idx"] = 0
    return {
        "dimensions": dict(zip(names, amounts, strict=True)), "fixed_corner_index": 0,
        "wrong_corner_refused": wrong_corner_refused,
        "plane": datum or {"read_owner": "Front Plane", "distance_mm": 0},
        "volume_mm3": volume, "area_mm2": area, "bounds_mm": [point(bounds.minimum), point(bounds.maximum)],
        "centre_mm": [low + length / 2 for low, length in zip(location, size, strict=True)],
        "counts": observed["counts"], "incidence_sha256": digest(wire(observed)),
        "sha256": digest(candidate.BytesValue), "bytes": len(candidate.BytesValue),
        "streams": {name: {"sha256": digest(data), "bytes": len(data)}
                    for name, data in archive.streams.items()},
    }


def rotated_shape(document, feature, source):
    actual, owner, _ = ReadStockSource(document, feature)
    props = owner.properties
    data = actual.entries[props["Shape"][0].attrib["file"]]
    assert digest(data) == source["shape_sha256"]
    shape = DecodeAsciiBrep(data)
    assert shape is not None and len(shape.vertices) == 8
    pl = props["Placement"][0].attrib
    raw_axis = tuple(float(pl[key]) for key in ("Ox", "Oy", "Oz"))
    magnitude = hypot(*raw_axis)
    assert 0 < magnitude < 1
    axis = tuple(component / magnitude for component in raw_axis)
    radians = float(pl["A"])
    assert isclose(sum(value * value for value in axis), 1, rel_tol=0, abs_tol=1e-14)
    world = []
    for local in product(*((0, value) for value in source["size_mm"])):
        vx, vy, vz = axis
        lx, ly, lz = local
        cross = (vy*lz-vz*ly, vz*lx-vx*lz, vx*ly-vy*lx)
        overlap = sum(a*b for a, b in zip(axis, local, strict=True))
        world.append(tuple(
            source["placement_mm"][index] + local[index]*cos(radians)
            + cross[index]*sin(radians) + axis[index]*overlap*(1-cos(radians))
            for index in range(3)
        ))
    actual = [point(vertex.point) for vertex in shape.vertices]
    assert all(sum(dist(observed, corner) < 1e-9 for observed in actual) == 1 for corner in world)
    return {"placement_rotation_rad": radians, "local_axis": axis,
            "stored_axis_norm": magnitude, "world_corner_count": len(world),
            "world_corners_sha256": digest(wire(sorted(world)))}


def compare(case, document, source, locator):
    owner, name, _ = SOURCES[case]
    feature = "freecad:feature:" + owner
    boundary = refuse_public(
        document, locator, ValueError, "native-only feature definitions cannot be exported"
    )
    if case == "C057-P01":
        return {
            "actual_rotation": rotated_shape(document, feature, source),
            "rotation_refused": reject(
                lambda: PrepFcStock(document, feature, locator, EPOCH, Placed=True),
                ValueError, "unsupported rigid rotation",
            ),
            "intact_public_refusals": boundary,
        }, None
    sizes = tuple(source["size_mm"])
    location = tuple(source["placement_mm"])
    plan = PlanFcStock(document, feature, name, Placed=True)
    assert point(plan.support_planes[0].transform.origin) == location
    assert not (plan.brep or plan.brep_payloads)
    if case == "standalone":
        assert len(document.feature_timeline) == len(document.bodies) == 1
        assert plan.bodies[0].id == document.bodies[0].id
    actual, source_owner, _ = ReadStockSource(document, feature)
    shape = ReadStockShape(document, actual, source_owner, feature, sizes,
                           Minimum=location, Placed=True)
    candidate = PrepFcStock(document, feature, locator, EPOCH, Placed=True)
    result = check_tool(shape, sizes, location, candidate, locator,
                        source["source_alias"], plan.bodies[0].id)
    refusal = (
        "unsupported typed offset-plane part" if case == "standalone"
        else "contains no readable Parasolid payload"
    )
    result["public_full_read_boundary"] = reject(
        lambda: open_document(candidate.BytesValue, source_format=FORMAT, strict=True),
        SldprtFormat, refusal,
    )
    if case == "C151-P01":
        design = open_document(candidate.BytesValue, source_format=FORMAT, strict=True, include_brep=False)
        assert set(value.name for value in design.parameters) == set(result["dimensions"])
        result["design_only_parameter_count"] = len(design.parameters)
    else:
        result["public_design_read_boundary"] = reject(
            lambda: open_document(candidate.BytesValue, source_format=FORMAT, strict=True, include_brep=False),
            SldprtFormat, refusal,
        )
    result["intact_public_refusals"] = boundary
    result["origin_only_refusal"] = reject(
        lambda: PrepFcStock(document, feature, locator, EPOCH),
        ValueError, "alternate attachment or placement",
    )
    return result, candidate.BytesValue


def worker(request):
    case = request["case"]
    path = Path(request["path"]).resolve(strict=True)
    compact = "".join(character for character in str(path).casefold() if character.isalnum())
    assert path.suffix.casefold() == ".fcstd"
    assert not any(marker in compact for marker in ("holdout", "heldout", "sealed"))
    owner, name, pin = SOURCES[case]
    raw = pinned(path, pin)
    prewarm()
    observations, denied = guard_source(path, ROOT / "src")
    document = open_document(path, source_format="freecad.fcstd", strict=True)
    assert observations and not denied and document.source.sha256 == pin
    prior = document.to_json(indent=None)
    count = len(observations)
    source = source_owners(raw, owner, case)
    locator = f"C:\\KitSdkCandidates\\{name}.SLDPRT"
    audit = WriterAudit(ROOT / "src", Path("Unused.SLDPRT"))
    sys.addaudithook(audit.observe)
    audit.phase = "prepare"
    try:
        result, payload = compare(case, document, source, locator)
        assert document.to_json(indent=None) == prior
    finally:
        audit.phase = "done"
    assert count == len(observations) and not denied and not audit.denied and not audit.target_opens
    assert pinned(path, pin) == raw
    if request["emit"] and payload is not None:
        result["scratch_b64"] = b64encode(payload).decode("ascii")
    return {
        "file_name": name + ".SLDPRT", "logical_locator": locator, "case": case,
        "source": source, "source_sha256": pin, "runtime_data_reads": 0,
        "original_neutral_unchanged": True, "result": result,
    }


def main(inventory, standalone, emit):
    request_rows = loads(pinned(inventory, INVENTORY))["files"]
    if emit is not None:
        assert not emit.resolve().is_relative_to(ROOT) and not emit.exists()
    outcomes = {}
    candidates = {}
    for case, (_, _, pin) in SOURCES.items():
        if case == "standalone":
            path = standalone
        else:
            row, = (value for value in request_rows if value["case_id"] == case)
            assert row["sha256"] == pin
            path = row["source_path"]
        requests = wire({"case": case, "path": str(path), "emit": emit is not None})
        children = [
            run((sys.executable, "-I", "-B", str(HERE), "--worker"),
                input=requests, capture_output=True, timeout=150) for worker_num in range(2)
        ]
        for child in children:
            if child.returncode or child.stderr:
                sys.stderr.buffer.write(child.stderr)
                raise ValueError(f"guarded placed stock case failed: {case}")
        assert children[0].stdout == children[1].stdout
        outcome = loads(children[0].stdout)
        if "scratch_b64" in outcome["result"]:
            payload = b64decode(outcome["result"].pop("scratch_b64"), validate=True)
            assert digest(payload) == outcome["result"]["sha256"]
            candidates[outcome["file_name"]] = payload
        outcomes[case] = outcome
    if emit is not None:
        emit.mkdir(exist_ok=False)
        for file_name, payload in candidates.items():
            with (emit / file_name).open("xb") as output:
                output.write(payload)
    return {
        "schema": "kit.sw2026.freecad-placed-stock.v1", "base": BASE, "creation_epoch": EPOCH,
        "inventory_sha256": INVENTORY, "fresh_workers": 2 * len(SOURCES),
        "cases": outcomes, "code_sha256": {str(path.relative_to(ROOT)): digest(path.read_bytes())
                                          for path in (*(ROOT / file for file in CODE), HERE)},
        "native_processes": 0, "heldout_cases": 0, "corpus_credit": 0, "public_qualified": False,
    }


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--standalone", type=Path)
    parser.add_argument("--candidate-dir", type=Path)
    args = parser.parse_args()
    if not args.worker and (args.inventory is None or args.standalone is None):
        parser.error("Both source custody paths are required.")
    sys.stdout.buffer.write(wire(
        worker(loads(sys.stdin.buffer.read())) if args.worker else
        main(args.inventory, args.standalone, args.candidate_dir)
    ))
