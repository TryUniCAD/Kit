from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
from json import dumps, loads
from math import isclose
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from VerifySdkCircleEndRegistration import OutputGuard

ROOT = Path(__file__).resolve().parents[3]
FORMAT = "solidworks.sldprt"
MEASURE = "solidworks_native_measurement"
DISCLOSED = ("radius", "diameter", "reverse-right", "mid-top", "two-front", "two-rev-top")


def digest(data):
    return sha256(data).hexdigest()


def report_inputs(case):
    old = case in DISCLOSED[:2]
    if old:
        filename = "SdkCircleNative01.json"
        expected = "bc49ba2f4fd8215f2772c16dc7bdfc7c973f2dcacc4214b4890ef2bdb8ad6be0"
    else:
        filename = "SdkCircleEndConditions01.json"
        expected = "9c0fdd3617ad06f1c7a7d90f3dd59f88794c80e22e7b5d7b54256c75d5a77a10"
    data = (ROOT / "re/solidworks/measurements/2026" / filename).read_bytes()
    assert digest(data) == expected
    return data.decode("utf-8"), old


def preload():
    for codec in ("utf-8", "utf-16-le", "latin-1", "cp1252"):
        lookup(codec)
    for module in ("interchange.brep.Validation.BrepValidate",
                   "interchange.document.Models.DocumentProvenance",
                   "interchange.document.Models.DocumentWalk",
                   "interchange.document.Validation.DocumentAssemblyValidate",
                   "interchange.document.Validation.DocumentFeatureValidate",
                   "interchange.document.Validation.DocumentReferenceValidate"):
        import_module(module)


def shape_points(value):
    return (value.x, value.y, value.z)


def check_projection(actual, source, native, full):
    from interchange.Features.FeatureExtrude import ExtrudeFeature
    from interchange.geometry.Models.GeometryCurves import CircleGeometry, PointGeometry

    actual.assert_valid()
    (sketch,), (body,) = actual.sketches, actual.bodies
    (feature,) = (row for row in actual.feature_timeline if row.id == body.final_feature_id)
    (support,) = (row for row in actual.support_planes if row.id == sketch.support_plane_id)
    (expected_feature,) = source.feature_timeline
    (expected_circle,) = source.sketches[0].entities
    (circle,) = (row for row in sketch.entities if isinstance(row.geometry, CircleGeometry))
    (point,) = (row for row in sketch.entities if isinstance(row.geometry, PointGeometry))
    assert len(sketch.entities) == 2 and point.geometry.point == circle.geometry.center
    assert sketch.closed_profile_entity_ids == ((circle.id,),)
    expected = expected_feature.definition
    assert isinstance(feature.definition, ExtrudeFeature) and feature.sketch_id == sketch.id
    assert feature.definition.end_condition == expected.end_condition
    assert feature.definition.reversed is expected.reversed
    assert feature.definition.symmetric is expected.symmetric
    assert support.name == source.support_planes[0].name
    assert support.transform == source.support_planes[0].transform
    for coordinate, intended in zip(
        (circle.geometry.center.x, circle.geometry.center.y, circle.geometry.radius),
        (expected_circle.geometry.center.x, expected_circle.geometry.center.y, expected_circle.geometry.radius),
        strict=True,
    ):
        assert isclose(coordinate, intended, rel_tol=1e-13, abs_tol=1e-14)
    kind = next(row for row in source.sketches[0].constraints if row.kind in ("diameter", "radius"))
    assert {row.kind for row in sketch.constraints} == {"fixed", kind.kind}
    fixed, radial_relation = (next(row for row in sketch.constraints if row.kind == value)
                              for value in ("fixed", kind.kind))
    assert tuple(ref.entity_id for ref in fixed.references) == (point.id,)
    assert tuple(ref.entity_id for ref in radial_relation.references) == (circle.id,)
    (radial,) = sketch.parameter_ids
    assert radial_relation.parameter_id == radial and fixed.parameter_id is None
    params = {row.id: row for row in actual.parameters}
    driver = params[radial]
    assert driver.owner_id in {sketch.id, *(
        row.id for row in actual.feature_timeline if row.sketch_id == sketch.id and row.id != feature.id
    )}
    source_params = {row.id: row for row in source.parameters}
    (source_radial,) = source.sketches[0].parameter_ids
    assert isclose(driver.value.value, source_params[source_radial].value.value, rel_tol=1e-13)
    depth_ids = feature.parameter_ids
    driver_count = (3 if expected.second_length is not None else 2)
    assert len(params) == driver_count and len(depth_ids) == driver_count - 1
    for number, current, wanted in zip(range(1, driver_count), depth_ids, expected_feature.parameter_ids, strict=True):
        saved = params[current]
        assert saved.owner_id == feature.id and saved.name == f"D{number}" and saved.value.unit == "mm"
        assert isclose(saved.value.value, source_params[wanted].value.value, rel_tol=1e-13)
    assert (actual.brep is not None) is full and not actual.brep_payloads
    if not full:
        return {"driver_count": driver_count}
    topology = body.topology
    assert not actual.brep.validate(frozenset((body.id,)))
    assert (topology.solid_count, topology.shell_count, topology.face_count, topology.edge_count) == (1, 1, 3, 2)
    assert format(topology.volume * 1e-9, ".6g") == format(native["volume"], ".6g")
    assert format(topology.surface_area * 1e-6, ".6g") == format(native["area"], ".6g")
    low, high = tuple(shape_points(point) for point in (topology.bounding_box.minimum, topology.bounding_box.maximum))
    center = tuple((a + b) * 0.0005 for a, b in zip(low, high, strict=True))
    assert all(isclose(a, b, rel_tol=5e-7, abs_tol=1e-12) for a, b in zip(center, native["com"], strict=True))
    primary = expected.length.value
    secondary = 0 if expected.second_length is None else expected.second_length.value
    if expected.symmetric:
        stations = (-primary * 0.5, primary * 0.5)
    else:
        stations = (-primary, secondary) if expected.reversed else (-secondary, primary)
    normal = shape_points(support.transform.z_axis)
    (axis,) = (index for index, value in enumerate(normal) if abs(value) == 1)
    global_stations = sorted(normal[axis] * value for value in stations)
    assert all(isclose(a, b, rel_tol=1e-13, abs_tol=1e-12)
               for a, b in zip((low[axis], high[axis]), global_stations, strict=True))
    return {"driver_count": driver_count, "stations_mm": stations, "volume_mm3": topology.volume,
            "area_mm2": topology.surface_area, "centroid_m": center, "faces": topology.face_count}


def prove(case, request, mode, authority, scratch):
    from convert import open_document, write_document
    from convert.adapters.base.GetDocumentCaps import GetDocumentCaps
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
    from convert.adapters.solidworks.Core.Preparation.Circle.PrepareCircle import PrepareCircle
    from convert.adapters.solidworks.Core.Writing.Circle.CanWriteCircle import HasCircWrite
    from convert.adapters.solidworks.Core.Writing.Circle.EmitCircMut import EmitCircMut
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
    from interchange.document.Models.DocumentModel import CadDocument
    from interchange.serialization.Deserialize import FromData

    original = FromData(request["document"])
    original.assert_valid()
    text = original.to_json(indent=None)
    restored = CadDocument.from_json(text)
    assert restored == original
    report_text, old = authority
    report = loads(report_text)
    name = original.metadata["name"]
    (row,) = (entry for entry in report["cases"] if entry["name"] == name)
    expected = row["candidate_sha256" if old else "artifact_sha256"]
    observed = (row["stages"][0] if old else row["native_phases"][0])
    native = (observed["snapshots"]["snapshot"]["mass_properties"] if old
              else observed["states"]["snapshot"]["mass"])
    leaf = name + ".SLDPRT"
    locator = "C:\\KitSdkCandidates\\" + leaf
    receipt = {"written_at": request["created_at"], "receipt": {"native_report": report_text}}
    values = {"final_destination": locator, MEASURE: receipt, "require_native_transfers": True, "allow_carrier": False}
    authored_caps = GetDocumentCaps(original)
    preload()
    guard = OutputGuard(scratch, leaf)
    sys.addaudithook(guard.audit)

    def private(doc, sink, fields):
        return EmitCircMut(doc, sink, WriteOptions(values=fields))

    def public(doc, sink, fields):
        return write_document(doc, sink, destination_format=FORMAT, allow_carrier=False, values=fields)

    def direct(doc, sink, fields):
        return SldprtWriter().write(doc, sink, WriteOptions(values=fields))

    def adapter(doc, sink, fields):
        return SldprtAdapter().write(doc, sink, WriteOptions(values=fields))

    routes = (private,) if mode == "leaf" else (public, direct, adapter)
    path = scratch / leaf
    path_values = {k: v for k, v in values.items() if k != "final_destination"}
    results = {}
    for route in routes:
        with guard.active("memory"):
            payload = PrepareCircle(original, BytesIO(), request["created_at"],
                                    WriteOptions(values=values), Measured=True).BytesValue
            assert digest(payload) == expected
            for doc in (original, restored):
                sink = BytesIO()
                result = route(doc, sink, values)
                assert sink.getvalue() == payload and result.vendor_loadable and result.application_usable
                assert result.metadata[MEASURE]["generated_sha256"] == expected
                assert authored_caps <= result.native_capabilities and not result.dropped and not result.carrier_capabilities
        with guard.active("path"):
            result = route(original, path, path_values)
        assert result.path == path and result.vendor_loadable and path.read_bytes() == payload
        assert tuple(scratch.iterdir()) == (path,)
        path.unlink()
        with guard.active("path"):
            refuse(route, original, path, {k: v for k, v in path_values.items() if k != MEASURE},
                   "offline native measurement")
        assert not tuple(scratch.iterdir())
        with guard.active("memory"):
            count = refuse_changes(route, original, values, name)
        results[route.__name__] = {"streams": 2, "paths": 1, "refusals": count + 1}
    with guard.active("memory"):
        assert scope_refusals(original, values, request["created_at"]) == 2
        archive = SldprtArchive.from_bytes(payload)
        streams = {key: digest(value) for key, value in archive.streams.items()}
        assert len(streams) == 10
        reads = {}
        for full in (True, False):
            native_doc = open_document(BytesIO(payload), source_format=FORMAT, strict=True, include_brep=full)
            assert CadDocument.from_json(native_doc.to_json(indent=None)) == native_doc
            assert not HasCircWrite(native_doc)
            reads[str(full)] = check_projection(native_doc, original, native, full)
    assert not guard.denied and not any(name.startswith(("pythoncom", "win32com")) for name in sys.modules)
    return {"case": case, "name": name, "archive_sha256": expected, "receipt_sha256": digest(report_text.encode()),
            "streams": streams, "routes": results, "reads": reads, "profile_refusals": 2,
            "runtime_input_file_reads": len(guard.denied),
            "native_calls": 0}


def refuse_changes(route, source, values, name):
    measurement = values[MEASURE]
    report = measurement["receipt"]["native_report"]
    step, = source.feature_timeline
    parameters = list(source.parameters)
    edit_slot = 0 if step.definition.second_length is None else len(parameters) - 1
    edit = parameters[edit_slot]
    value = replace(edit.value, value=edit.value.value + 0.375)
    parameters[edit_slot] = replace(edit, value=value)
    definition = (replace(step.definition, length=value) if step.definition.second_length is None
                  else replace(step.definition, second_length=value))
    changed = replace(source, parameters=tuple(parameters), feature_timeline=(replace(step, definition=definition),))
    contrasts = (
        (changed, values, "no matching exact native measurement"),
        (source, {k: v for k, v in values.items() if k != MEASURE}, "offline native measurement"),
        (source, {**values, MEASURE: {**measurement, "written_at": measurement["written_at"] + 1}}, "no matching exact native measurement"),
        (source, {**values, MEASURE: {**measurement, "receipt": {"native_report": report + " "}}}, "authenticated offline evidence"),
        (source, {**values, "final_destination": "C:\\Different\\%s.SLDPRT" % name}, "no matching exact native measurement"),
    )
    for doc, fields, expected in contrasts:
        sink = BytesIO()
        refuse(route, doc, sink, fields, expected)
        assert sink.getvalue() == b"" and sink.tell() == 0
    return len(contrasts)


def refuse(route, document, sink, fields, expected):
    try:
        route(document, sink, fields)
    except ValueError as error:
        assert expected in str(error), (expected, str(error))
    else:
        raise AssertionError("unmeasured or unsupported circle escaped publication")


def scope_refusals(source, values, event):
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Core.Preparation.Circle.PrepareCircle import PrepareCircle

    step, = source.feature_timeline
    plane, = source.support_planes
    reversed_end = replace(step.definition, reversed=not step.definition.reversed)
    moved_origin = replace(plane.transform.origin, x=2.0)
    moved_plane = replace(plane, transform=replace(plane.transform, origin=moved_origin))
    contrasts = (
        (replace(source, feature_timeline=(replace(step, definition=reversed_end),)), "not qualified"),
        (replace(source, support_planes=(moved_plane,)), "canonical principal frame"),
    )
    settings = WriteOptions(values={k: v for k, v in values.items() if k != MEASURE})
    for changed, expected in contrasts:
        sink = BytesIO()
        refuse(lambda document, target, options:
               PrepareCircle(document, target, event, options, Measured=True),
               changed, sink, settings, expected)
        assert sink.getvalue() == b""
    return len(contrasts)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--case", choices=DISCLOSED, required=True)
    parser.add_argument("--requests", type=Path, required=True)
    parser.add_argument("--sdk", type=Path, default=ROOT / "src")
    parser.add_argument("--route", choices=("leaf", "public"), default="leaf")
    args = parser.parse_args()
    sys.path[:0] = [str(args.sdk.resolve()), str(ROOT)]
    with TemporaryDirectory(prefix="KitCircleEndPort-") as folder:
        request = loads((args.requests / (args.case + ".json")).read_bytes())
        result = prove(args.case, request, args.route, report_inputs(args.case), Path(folder).resolve())
    print(dumps(result, sort_keys=True, allow_nan=False))
