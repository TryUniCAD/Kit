from argparse import ArgumentParser
from codecs import lookup
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
from json import dumps, loads
from math import cos, isclose, pi, sin
from pathlib import Path, PureWindowsPath
from platform import python_version
from subprocess import run
from tempfile import TemporaryDirectory
import sys
import zlib

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT / "src"), str(HERE.parent.parent)]

from ProveCircleEndPort import OutputGuard, preload
from convert import open_document, write_document
from convert.adapters.base.GetDocumentCaps import GetDocumentCaps
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Container.Container import SldprtArchive, build_sldprt
from convert.adapters.solidworks.Container.Format import KGhostPartition, KPartitionStream
from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
from convert.adapters.solidworks.Core.Preparation.Sweeps.BuildSweepPart import BuildSweepPart
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Cold.ReadColdIntent import ReadColdIntent
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwGraph import ReadSwGraph
from convert.adapters.solidworks.Core.Writing.CanWriteSweep import CanWriteSweep
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange.brep.Curves.BrepPcurves import CirclePcurve, LinePcurve
from interchange.brep.Surfaces.BrepSurfaces import PlaneSurface, TorusSurface
from interchange.Features.SweepFeature import SweepFeature


BASE = "ffa49a63caf2b3c433c05433c7b638e5d0d4fde7"
NATIVE = "380ead8ff07a9337bd0df87d32eb92e49529e0579c15449767a5ee26e53dd512"
MEASURED = "fc098693d77e0e41e5652eed80fe705b528db9cb9f6ac527fb379784087d83d0"
SAVED = "48489d730ec369b90589484407b62a63134958c6a039172b8751a0c3e0fb9544"
TOOLING = ROOT / "re/solidworks/measurements/2026"
FORMAT = "solidworks.sldprt"
JSON = "interchange.json"
MEASUREMENT = "solidworks_native_measurement"


def digest(data):
    return sha256(data).hexdigest()


def locked(path, expected):
    data = path.read_bytes()
    assert digest(data) == expected, path.name
    return data


def reject(expect, operation):
    try:
        operation()
    except ValueError as error:
        assert expect in str(error), (expect, str(error))
    else:
        raise ValueError("unqualified sweep entered the scoped route")


def public(document, sink, values):
    return write_document(document, sink, destination_format=FORMAT, allow_carrier=False, values=values)


def adapter(document, sink, values):
    return SldprtAdapter().write(document, sink, WriteOptions(values=values))


def direct(document, sink, values):
    return SldprtWriter().write(document, sink, WriteOptions(values=values))


def coordinates(vector):
    return vector.x, vector.y, vector.z


def check_rims(model, radius, path):
    caps = tuple(row for row in model.surfaces if isinstance(row, PlaneSurface))
    torus, = (row for row in model.surfaces if isinstance(row, TorusSurface))
    assert tuple(coordinates(row.normal) for row in caps) == ((-1, 0, 0), (0, 1, 0))
    assert tuple(coordinates(row.origin) for row in caps) == ((0, 0, 0), (path, path, 0))
    assert (coordinates(torus.center), torus.major_radius, torus.minor_radius) == ((0, path, 0), path, radius)
    assert coordinates(torus.axis) == (0, 0, 1) and coordinates(torus.reference_direction) == (0, -1, 0)
    assert len(model.vertices) == 2 and all(row.attributes.get("periodic_seam") is True for row in model.vertices)
    trims = {row.id: row for row in model.pcurves}
    for index, (edge, circle, cap, station, sign) in enumerate(zip(
        model.edges, model.curves, caps, (0, pi / 2), (1, -1), strict=True
    )):
        assert edge.start_vertex_id == edge.end_vertex_id and edge.start_parameter == 0
        assert edge.end_parameter == 2 * pi and edge.curve_id == circle.id and circle.radius == radius
        assert circle.center == cap.origin and circle.axis == cap.normal
        assert circle.reference_direction == cap.reference_direction
        assert coordinates(circle.reference_direction) == ((0, -1, 0), (1, 0, 0))[index]
        cap_use, wall_use = (row for row in model.coedges if row.edge_id == edge.id)
        assert not cap_use.reversed and wall_use.reversed
        cap_uv, wall_uv = trims[cap_use.pcurve_id], trims[wall_use.pcurve_id]
        assert isinstance(cap_uv, CirclePcurve) and cap_uv.radius == radius
        assert isinstance(wall_uv, LinePcurve) and (wall_uv.origin.x, wall_uv.origin.y) == (station, 0)
        assert (wall_uv.direction.x, wall_uv.direction.y) == (0, sign)
        for angle in (0, pi / 2, pi, 3 * pi / 2):
            radial = path + radius * cos(angle)
            point = (radial * sin(station), path - radial * cos(station), radius * sin(sign * angle))
            expected = (
                (0, -radius * cos(angle), radius * sin(angle))
                if index == 0 else (path + radius * cos(angle), path, -radius * sin(angle))
            )
            assert all(isclose(a, b, rel_tol=1e-13, abs_tol=1e-12) for a, b in zip(point, expected, strict=True))


def check_cold(document, state, observations, include):
    section, path = document.sketches
    feature, = document.feature_timeline
    body, = document.bodies
    diameter, radius, density = document.parameters
    assert type(feature.definition) is SweepFeature
    assert (feature.sketch_id, feature.definition.PathSketchId) == (section.id, path.id)
    assert feature.output_body_ids == (body.id,) and body.final_feature_id == feature.id
    assert "native_atom_id" not in body.attributes and not document.brep_payloads and not document.diagnostics
    assert document.source.attributes["cold_sweep_model"] is True and "saved_sweep_result" not in document.source.attributes
    assert (section.name, path.name) == ("SweepSection", "SweepPath")
    assert (diameter.owner_id, radius.owner_id, density.owner_id) == (section.id, path.id, body.id)
    assert (diameter.value.value / 1000, radius.value.value / 1000) == (
        state["section_diameter_m"], state["path_radius_m"]
    )
    assert density.value.value == 1031.7 and density.value.unit == "kg/m3"
    assert diameter.name == radius.name == "D1"
    for driver, sketch, kind, identity in zip((diameter, radius), document.sketches, ("diameter", "radius"),
                                             ((25, 174, 172, 6221, 6287), (27, 196, 195, 9359, 9402)), strict=True):
        relation, = (row for row in sketch.constraints if row.kind == kind)
        assert relation.driving and relation.parameter_id == driver.id and sketch.parameter_ids == (driver.id,)
        assert relation.references[0].entity_id == sketch.entities[0].id
        owner = driver.attributes["typed_archive_owner"]
        assert owner["stream"] == "Contents/Config-0-ResolvedFeatures" and owner["value_field"] == "f58"
        assert tuple(owner[key] for key in ("dimension_id", "object_index", "dimension_index", "offset", "end")) == identity
    span, = density.provenance.spans
    assert (span.stream, span.offset, span.offset + span.length) == ("Contents/Config-0", 2068, 2127)
    assert not density.provenance.native_id
    topology = body.topology
    assert (topology.solid_count, topology.face_count, topology.edge_count, topology.vertex_count) == (
        state["solid_count"], observations["faces"], observations["edges"], observations["vertices"]
    )
    section_mm, path_mm = state["section_diameter_m"] * 500, state["path_radius_m"] * 1000
    assert coordinates(topology.bounding_box.minimum) == (0, -section_mm, -section_mm)
    assert coordinates(topology.bounding_box.maximum) == (path_mm + section_mm, path_mm, section_mm)
    reported = (topology.volume * 1e-9, topology.surface_area * 1e-6, body.attributes["mass_kg"],
                *(value / 1000 for value in body.attributes["center_of_mass_mm"]))
    measured = (state["volume_m3"], state["area_m2"], state["mass_kg"], *state["com_m"])
    assert all(format(a, ".6g") == format(b, ".6g") if abs(b) > 1e-12 else abs(a - b) < 1e-12
               for a, b in zip(reported, measured, strict=True))
    face_areas = (pi * (section_mm / 1000) ** 2,) * 2 + (pi ** 2 * section_mm * path_mm * 1e-6,)
    assert all(row["torus"] is (index == 2) and row["producer"] == feature.name
               and format(row["area_m2"], ".6g") == format(area, ".6g")
               for index, (row, area) in enumerate(zip(observations["face_rows"], face_areas, strict=True)))
    assert (document.brep is not None) is include
    if include:
        model = document.brep
        assert not model.validate(frozenset({body.id})) and model.bodies[0].design_body_id == body.id
        assert (len(model.faces), len(model.edges), len(model.pcurves)) == (3, 2, 4)
        check_rims(model, section_mm, path_mm)
    return {"measurements_checked": len(measured), "native_face_owners_checked": 3, "analytic_rim_points_checked": 8 if include else 0}


def reject_writes(document, values):
    stale = deepcopy(values)
    stale[MEASUREMENT]["receipt"]["cases"][0]["archive_sha256"] = "0" * 64
    stale[MEASUREMENT]["receipt"]["cases"][1]["archive_sha256"] = "f" * 64
    body, = document.bodies
    section, path = document.sketches
    entity, = section.entities
    feature, = document.feature_timeline
    wrong_seam = replace(section, entities=(replace(entity, attributes={}),))
    contrasts = (
        ("source_digest", replace(document, source=replace(document.source, sha256="0" * 64)), values, "differs from its regenerated part"),
        ("body_topology", replace(document, bodies=(replace(body, topology=replace(body.topology, edge_count=3)),)), values, "differs from its regenerated part"),
        ("source_seam", replace(document, sketches=(wrong_seam, path)), values, "differs from its regenerated part"),
        ("output_relation", replace(document, feature_timeline=(replace(feature, OutputBodyIds=()),)), values, "differs from its regenerated part"),
        ("stale_measurement", document, stale, "no unique exact native measurement"),
        ("changed_locator", document, values | {"final_destination": values["final_destination"].replace("Candidates", "Other")}, "no unique exact native measurement"),
        ("missing_measurement", document, {key: value for key, value in values.items() if key != MEASUREMENT}, "requires an offline native measurement"),
    )
    for label, changed, options, diagnostic in contrasts:
        for publish in (public, adapter, direct):
            sink = BytesIO(b"untouched")
            reject(diagnostic, lambda: publish(changed, sink, options))
            assert sink.getvalue() == b"untouched" and sink.tell() == 0, label
    return [row[0] for row in contrasts]


def prove_cold(raw, job):
    case = job["case"]
    name = PureWindowsPath(case["locator"]).name
    archive = SldprtArchive.from_bytes(raw)
    assert archive.get(KPartitionStream) is None and archive.get(KGhostPartition) is not None
    graph = ReadSwGraph(archive, ColdSweep=True)
    intent = ReadColdIntent(graph)
    assert graph.DensityValue.FieldsValue["f08"] == -1
    assert (NativeNodeId(graph.ConfigValue), intent.OutputValue.PathName, intent.OutputValue.SavedAt) == (
        0, case["locator"], case["written_at"]
    )
    assert BuildSweepPart(intent).BytesValue == raw
    stream_hashes = {row.name: digest(row.data) for row in archive.records}
    assert stream_hashes == job["streams"]
    missing = {key: value for key, value in archive.streams.items() if key != KGhostPartition}
    foreign = SldprtArchive.from_bytes(bytes.fromhex(job["foreign"]))
    variants = (
        ("missing_ghost", missing, "GhostPartition"),
        ("other_path_ghost", archive.streams | {KGhostPartition: foreign.require(KGhostPartition)}, "unsupported SOLIDWORKS cold sweep"),
        ("extra_source_stream", archive.streams | {"Contents/UnmodeledSweepState": b"metadata"}, "canonical sweep reconstruction differs"),
    )
    for _, streams, message in variants:
        wire = build_sldprt(streams, FormatVersion=4)
        for include in (True, False):
            reject(message, lambda: open_document(wire, include_brep=include, configuration="Default"))
            reject(message, lambda: SldprtAdapter().read(wire, ReadOptions(include_brep=include)))
    assert not SldprtAdapter().read(raw, ReadOptions(extract_raw_brep=True)).source.attributes.get("cold_sweep_model")
    values = {"final_destination": case["locator"], "require_native_transfers": True, "require_self_contained": True,
              "allow_carrier": False, MEASUREMENT: {"written_at": case["written_at"], "receipt": job["receipt"]}}
    projections = {}
    for include in (True, False):
        document = open_document(BytesIO(raw), source_format=FORMAT, include_brep=include)
        assert document == SldprtAdapter().read(BytesIO(raw), ReadOptions(include_brep=include, configuration="Default"))
        assert document == open_document(BytesIO(raw), source_format=FORMAT, include_brep=include, strict=False)
        assert document.source.sha256 == case["archive_sha256"]
        result = check_cold(document, case["states"][0], job["native_topology"], include)
        portable = BytesIO()
        write_document(document, portable, destination_format=JSON, allow_carrier=False)
        reloaded = open_document(BytesIO(portable.getvalue()), source_format=JSON)
        assert reloaded.to_json(indent=None) == document.to_json(indent=None)
        for publish in (public, adapter, direct):
            sink = BytesIO()
            outcome = publish(reloaded, sink, values)
            assert sink.getvalue() == raw and outcome.bytes_written == len(raw)
            assert outcome.vendor_loadable and outcome.application_usable and not outcome.dropped and not outcome.carrier_capabilities
            assert outcome.native_capabilities == GetDocumentCaps(document)
            assert outcome.metadata[MEASUREMENT]["generated_sha256"] == case["archive_sha256"]
        projections["full" if include else "design"] = result | {
            "neutral_sha256": digest(document.to_json(indent=None).encode()), "native_transfers": len(document.capabilities),
            "exact_writes": 3, "refusals_checked_on_three_routes": reject_writes(reloaded, values),
        }
    return {"file": name, "sha256": digest(raw), "bytes": len(raw), "streams": stream_hashes, "projections": projections,
            "native_candidate_open_sha256": job["native_open_sha256"], "refused_read_variants": [row[0] for row in variants]}


def prove_saved(raw, job):
    case = job["case"]
    assert SldprtArchive.from_bytes(raw).get(KPartitionStream) is not None
    reader = SldprtAdapter()
    document = reader.read(raw, ReadOptions())
    digest_value = digest(document.to_json(indent=None).encode())
    assert digest_value == case["neutral_json_sha256"], (case["role"], digest_value, case["neutral_json_sha256"])
    for include in (True, False):
        document = open_document(BytesIO(raw), source_format=FORMAT, include_brep=include, configuration="Default")
        assert document.source.attributes["saved_sweep_result"] is True and "cold_sweep_model" not in document.source.attributes
        (body,) = document.bodies
        assert body.attributes["native_atom_id"] == str(case["source_observation"]["typed_result_atom"])
        assert (document.brep is not None) is include and not CanWriteSweep(document, BytesIO())
    return {"slot": case["slot"], "role": case["role"], "sha256": digest(raw),
            "unchanged_full_projection_sha256": digest_value, "saved_atom": int(body.attributes["native_atom_id"]),
            "strict_read_modes": 2, "cold_admission_refusals": 2}


def worker(job):
    raw = bytes.fromhex(job["raw"])
    expected = job["case"].get("archive_sha256", job["case"].get("source_sha256"))
    assert digest(raw) == expected
    preload()
    lookup("utf-8-sig")
    import_module("interchange.document.Models.FilterMetadata")
    with TemporaryDirectory(prefix="KitSweepRead") as folder:
        guard = OutputGuard(Path(folder), "guard")
        sys.addaudithook(guard.audit)
        with guard.active("stream"):
            result = (prove_saved if job["saved"] else prove_cold)(raw, job)
        assert not guard.denied and not any(name.startswith(("pythoncom", "win32com")) for name in sys.modules)
    return result | {"runtime_file_opens_and_processes": len(guard.denied)}


def isolated(job):
    process = run([sys.executable, "-I", "-B", str(HERE), "--worker"], input=dumps(job), capture_output=True,
                  text=True, timeout=90, check=False)
    assert process.returncode == 0 and not process.stderr, process.stderr
    return loads(process.stdout)


def supervise(cold, saved, output):
    authority = loads(locked(cold / "DisclosedRecords/Result.json", NATIVE))
    assert authority["passed"] and authority["inputs_unchanged"] and authority["distinct_processes"] == 12
    assert all(control["passed"] for control in authority["controls"].values())
    receipt = loads(locked(TOOLING / "SdkStandardSweepReceipt01.json", MEASURED))
    earlier = loads(locked(TOOLING / "AggregateSavedSweepRead01.json", SAVED))
    files = [locked(cold / "Packet/Candidates" / PureWindowsPath(case["locator"]).name, case["archive_sha256"])
             for case in receipt["cases"]]
    results = []
    for index, (case, native, baseline) in enumerate(zip(
        receipt["cases"], authority["cases"], earlier["cold_writer_baseline_and_port"]["records"], strict=True
    )):
        phase, = (row for row in native["phases"] if row["phase"] == "candidate-open")
        observation = loads(locked(cold / f"DisclosedRecords/Slot{index + 1:02}/candidate-open/Record.json", phase["receipt_sha256"]))
        assert phase["passed"] and native["candidate_sha256"]["original"] == phase["artifact_sha256"] == case["archive_sha256"]
        results.append(isolated({"saved": False, "raw": files[index].hex(), "case": case, "receipt": receipt,
                                 "foreign": files[1 - index].hex(), "streams": baseline["streams"],
                                 "native_open_sha256": phase["receipt_sha256"],
                                 "native_topology": observation["before_explicit_rebuild"]["topology"]}))
    kept = []
    for case in earlier["strict_saved_worker_observations"]:
        name = ("SweepArcNear", "SweepArcWide")[case["slot"] - 1]
        suffix = {"original": "", "section": "SectionEdit", "path": "PathEdit"}[case["role"]]
        raw = locked(saved / f"{name}{suffix}.SLDPRT", case["source_sha256"])
        kept.append(isolated({"saved": True, "raw": raw.hex(), "case": case}))
    proof = {"schema": "kit.sw2026.cold-sweep-readback.v1", "base": BASE, "python": python_version(),
             "zlib": zlib.ZLIB_RUNTIME_VERSION, "native_build": authority["oracle_build"],
             "native_result_sha256": NATIVE, "normalized_receipt_sha256": MEASURED, "warm_baseline_sha256": SAVED,
             "cold_generated": results, "saved_native": kept, "guarded_processes": len(results) + len(kept),
             "native_launches": 0, "new_heldout_credit": 0, "method_sha256": digest(HERE.read_bytes()),
             "src_tree": run(["git", "write-tree", "--prefix=src/"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()}
    with output.open("x", encoding="utf-8") as stream:
        stream.write(dumps(proof, indent=2, sort_keys=True) + "\n")
    print(digest(output.read_bytes()))


if __name__ == "__main__":
    if sys.argv[1:] == ["--worker"]:
        print(dumps(worker(loads(sys.stdin.read())), allow_nan=False))
    else:
        parser = ArgumentParser()
        parser.add_argument("--cold", required=True, type=Path)
        parser.add_argument("--saved", required=True, type=Path)
        parser.add_argument("--output", required=True, type=Path)
        args = parser.parse_args()
        supervise(args.cold, args.saved, args.output)
