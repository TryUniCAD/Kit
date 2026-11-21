from argparse import ArgumentParser
from dataclasses import replace
from io import BytesIO
from math import isclose
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory
import json
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))
import MeasureWarmNestedLeaf as warm
from VerifyFreecadF14aIntact import no_runtime_io, wire

from convert import open_document, write_document
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismBoss import CheckPrismBoss
from interchange.document.Behavior import DocumentIo
from interchange.Features.ScopedExtrude import ScopedExtrude
from interchange.serialization.EncodeData import ToData


BASIS = "2ae51b48574a9eee52213ce1af5bb76a2bd4c99b"
AUTHORITY = "re/solidworks/measurements/2026/FirstCreatorScopeAcceptance01.json"
AUTHORITY_SHA = "90d4d1836492f49fd2d6c99a122664c5be918d128dcd1c604a589d2ea724fa21"
JSON_FORMAT = "interchange.json"
GEOMETRY = "src/convert/adapters/solidworks/Core/TypedResolved/Geometry"
VALIDATION = "src/interchange/document/Validation"
SOURCES = (
    *(f"{GEOMETRY}/{name}.py" for name in (
        "CheckPrismAtom", "CheckPrismBoss", "CheckPrismScope", "CheckPrismRoots", "CheckPrismRoot",
        "ReadPrismPlan", "ReadPrismFrame", "ReadNoCache", "IsCacheAbsent", "ColdOutput/CheckColdBind",
        "ColdOutput/BindPrismCreate", "ColdOutput/WithColdName",
    )),
    "src/interchange/Features/ScopedExtrude.py",
    f"{VALIDATION}/FirstScopeErrs.py", f"{VALIDATION}/DocumentFeatureValidate.py",
    "re/tooling/sw2026/VerifyFreecadF14aIntact.py",
    "re/tooling/sw2026/nested_publication/MeasureWarmNestedLeaf.py",
    "re/tooling/sw2026/nested_publication/WarmLeafBoundary.py",
    HERE.relative_to(warm.ROOT).as_posix(),
)


def read_owners(raw):
    archive = warm.SldprtArchive.from_bytes(raw)
    link = warm.ReadNativeLink(archive, 0)
    features = warm.IndexFeatures(link)
    warm.CheckSingleBoss(features, "moExtrusion_c")
    boss, = (item for item in features.values() if item.ClassValue.NameValue == "moExtrusion_c")
    owner = warm.ReadExtrude(link, boss, features)
    return archive, link, owner


def body_and_step(document):
    body, = document.bodies
    step, = (row for row in document.feature_timeline if row.id == body.final_feature_id)
    return body, step


def verify_drivers(document, step, state, prior):
    features = {row.id: row for row in document.feature_timeline}
    assert document.configurations[0].name == state["configuration"] and not step.suppressed
    assert not step.selection_ids and all(row.query.get("role") != "extrusion_scope" for row in document.selections)
    profile, = document.sketches
    parent, = step.input_feature_ids
    assert profile.id == step.sketch_id == features[parent].sketch_id
    dims = {f"{row.name}@{features[row.owner_id].name}": row for row in document.parameters}
    assert dims.keys() == state["dimensions_m"].keys() and len(dims) == 3
    assert all(row.role.value == "driving" and row.expression is None and row.value.kind.value == "length"
               and row.value.unit == "mm" and isclose(row.value.value / 1000, state["dimensions_m"][name], rel_tol=1e-12)
               for name, row in dims.items())
    assert [int(value.rsplit(":", 1)[1]) for value in (parent, step.id)] == state["native_ids"] == [
        prior["typed_profile_id"], prior["typed_feature_id"]]
    constraints = {row.parameter_id for row in profile.constraints if row.kind == "distance"}
    assert set(profile.parameter_ids) == constraints and len(constraints) == 2
    assert len(profile.closed_profile_entity_ids) == 1 and len(profile.closed_profile_entity_ids[0]) == 4
    depth, = (row for row in dims.values() if row.owner_id == step.id)
    if isinstance(step.definition, ScopedExtrude):
        independent = step.definition.Extrusion
    else:
        independent = step.definition
    assert type(independent) is warm.ExtrudeFeature and independent.length == depth.value
    assert step.parameter_ids == (depth.id,) and independent.end_condition is warm.ExtrudeEnd.KBlind
    assert independent.reversed is False and independent.direction is None
    return depth, {name: {"id": row.id, "owner": row.owner_id, "mm": row.value.value} for name, row in dims.items()}


def verify_geometry(document, body, points, depth, state):
    shape = document.brep
    assert shape is not None and len(shape.bodies) == 1
    assert state["body_count"] == 1 and state["solid"]["topology"] == [6, 12, 8]
    geometry = warm.measure_boundary(shape, body.id, tuple(map(tuple, points)), depth.value.value, state["solid"]["mass"])
    limits = tuple(tuple(float(point) * 1000 for point in row) for row in state["solid"]["bounds_m"])
    actual = tuple(zip(*geometry["bounds_mm"], strict=True))
    assert all(isclose(a, b, rel_tol=1e-12, abs_tol=1e-10)
               for vector, expected in zip(actual, limits, strict=True)
               for a, b in zip(vector, expected, strict=True))
    return geometry


def rejected(action, diagnostic):
    try:
        action()
    except ValueError as error:
        if diagnostic in str(error):
            return diagnostic
        raise
    raise ValueError(f"expected refusal: {diagnostic}")


def archive_refusals(owner):
    def check(**fields):
        claimed = replace(owner.NodeValue, FieldsValue=owner.NodeValue.FieldsValue | fields)
        CheckPrismBoss(replace(owner, NodeValue=claimed), AllowFirstScope=True)

    return {
        "unknown_scope_word": rejected(lambda: check(f544=2), "atom attachment or modifier flags"),
        "picked_body_wrapper": rejected(lambda: check(has_f548=1), "atom attachment or modifier flags"),
        "hidden_wrapper_object": rejected(lambda: check(f548=owner.ProfileValue), "stored body owners"),
        "stored_output_flag": rejected(lambda: check(has_f528=1), "atom attachment or modifier flags"),
        "noncreate_flags": rejected(lambda: check(f810=0), "ordinary create boss mode"),
        "extra_parent": rejected(
            lambda: CheckPrismBoss(replace(owner, ParentsValue=(owner.ProfileValue, owner.NodeValue)), AllowFirstScope=True),
            "requires one ordinary forward blind profile"),
        "reverse_flag": rejected(lambda: CheckPrismBoss(replace(owner, IsReversed=True), AllowFirstScope=True),
                                 "requires one ordinary forward blind profile"),
    }


def json_refusals(document, creator, depth):
    def wrong_step(**fields):
        wrong = replace(creator, **fields)
        change = replace(document, feature_timeline=tuple(wrong if item is creator else item for item in document.feature_timeline))
        DocumentIo.FromJson(type(document), change.to_json())

    invalid = replace(depth, expression=warm.FromData({"$type": "Expression", "source": "2"}))
    alternate = replace(document, parameters=tuple(invalid if row is depth else row for row in document.parameters))
    earlier = replace(creator, id="earlier-creator", order=-1, definition=None)
    prior = replace(document, feature_timeline=(earlier, *document.feature_timeline))
    return {
        "legacy_empty_explicit": rejected(lambda: ScopedExtrude(creator.definition.Extrusion, "explicit", (), ()),
                                           "explicit scope requires selected body IDs"),
        "legacy_nonempty_explicit": ScopedExtrude(creator.definition.Extrusion, "explicit", ("one-body",), ()).ScopeMode,
        "first_mode_selected_body": rejected(
            lambda: replace(creator.definition, SelectedBodyIds=(document.bodies[0].id,)), "requires empty prior body lists"),
        "first_mode_reversed": rejected(lambda: replace(creator.definition, Extrusion=replace(creator.definition.Extrusion, reversed=True)),
                                        "requires one ordinary forward blind end"),
        "cut": rejected(lambda: wrong_step(operation=warm.BooleanOp.KCutOperation), "requires one active root solid extrusion"),
        "different_producer": rejected(lambda: wrong_step(operation=warm.BooleanOp.KJoin), "requires one active root solid extrusion"),
        "suppression": rejected(lambda: wrong_step(suppressed=True), "requires one active root solid extrusion"),
        "nonlocal_parent": rejected(lambda: wrong_step(input_feature_ids=(document.support_planes[0].id.replace(":plane:", ":feature:"),)),
                                    "inputs must own its profile sketch"),
        "picked_direction": rejected(lambda: wrong_step(selection_ids=(document.selections[0].id,)),
                                    "requires one active root solid extrusion"),
        "wrong_plane_normal": rejected(lambda: wrong_step(definition=replace(
            creator.definition, Extrusion=replace(creator.definition.Extrusion, direction=type(document.support_planes[0].transform.z_axis)(0, 0, -1)))),
            "requires its profile plane's forward direction"),
        "prior_solid": rejected(lambda: DocumentIo.FromJson(type(document), prior.to_json()), "earlier solid operation"),
        "alternate_depth": rejected(lambda: DocumentIo.FromJson(type(document), alternate.to_json()), "requires its actual live depth owner"),
    }


def cold_read(raw, job):
    archive, link, owner = read_owners(raw)
    boss = owner.NodeValue
    assert boss.FieldsValue["f544"] == job["scope"] and boss.FieldsValue.get("f548") is None
    assert link.ConfigValue.RootValue.FieldsValue["fd88"]["n6c"] == 0 and archive.get(warm.PARTITION) is None
    document = open_document(BytesIO(raw), source_format=warm.FORMAT, strict=True)
    body, creator = body_and_step(document)
    assert creator.operation == warm.BooleanOp.KCreate and not document.brep_payloads
    selected = isinstance(creator.definition, ScopedExtrude)
    assert selected == bool(job["scope"])
    independent = creator.definition.Extrusion if selected else creator.definition
    if selected:
        assert creator.definition.ScopeMode == "first_creator"
        assert creator.definition.SelectedBodyIds == creator.definition.AffectedBodyIds == ()
    depth, bindings = verify_drivers(document, creator, job["initial"], job["saved_proof"])
    actual_geometry = verify_geometry(document, body, job["points_mm"], depth, job["initial"])
    assert len(document.bodies) == 1 and body.topology.valid
    assert isclose(body.topology.volume, actual_geometry["volume_mm3"], rel_tol=1e-12)
    assert isclose(body.topology.surface_area, actual_geometry["surface_area_mm2"], rel_tol=1e-12)
    displays = warm.observe(raw, job["profile"])
    assert [displays[axis]["text_m"] for axis in ("width", "height")] == job["labels"]
    assert all(row["centerline_route"] is job["label_routing"] for row in displays.values())
    before = document.to_dict()
    serialized = (document.to_json() + "\n").encode()
    assert open_document(BytesIO(serialized), source_format=JSON_FORMAT, strict=True).to_dict() == before
    pair = ToData((document.parameters, document.support_planes, document.sketches, document.selections, document.bodies,
                   document.brep, tuple(replace(item, definition=independent) if item is creator else item
                                        for item in document.feature_timeline)))
    result = {"sha256": warm.digest(raw), "portable_scope": creator.definition.ScopeMode if selected else None,
              "scope_word": job["scope"], "operation": creator.operation.value, "geometry": actual_geometry,
              "feature_tree_rows": len(document.feature_timeline), "portable_pair_model_sha256": warm.digest(wire(pair)),
              "editable_driver_bindings": bindings, "stored_spatial_labels_m": job["labels"], "strict_json_stream_exact": True}
    if selected:
        result |= {"typed_archive_refusals": archive_refusals(owner), "portable_model_refusals": json_refusals(document, creator, depth)}
    return document, serialized, result


def saved_read(raw, job):
    archive, link, owner = read_owners(raw)
    proof, state = job["saved_proof"], job["reopened"]
    document = open_document(BytesIO(raw), source_format=warm.FORMAT, strict=True)
    body, creator = body_and_step(document)
    assert type(creator.definition) is warm.ExtrudeFeature and creator.operation == warm.BooleanOp.KJoin
    assert document.brep_payloads and archive.get(warm.PARTITION) is not None
    assert owner.NodeValue.FieldsValue["f544"] == proof["stored_existing_body_scope"] == job["scope"]
    assert owner.NodeValue.FieldsValue.get("f548") is None and proof["selected_wrapper_present"] == 0
    output = warm.ReadOutputAtom(owner.NodeValue)
    assert output.FieldsValue["f140"] == proof["actual_sole_body_atom_id"]
    assert link.ConfigValue.RootValue.FieldsValue["fd88"]["atoms"][0]["o"] is output
    _, _, marks = warm.ReadBodyKernel(archive.require(warm.PARTITION), warm.PARTITION)
    warm.CheckThinMarks(link.ConfigValue.RootValue, owner.NodeValue, marks)
    assert list(marks) == proof["typed_marks"]
    depth, bindings = verify_drivers(document, creator, state, proof)
    assert isclose(depth.value.value / 1000, proof["typed_depth_m"], rel_tol=1e-12)
    geometry = verify_geometry(document, body, job["points_mm"], depth, state)
    return {"sha256": warm.digest(raw), "strict_saved_cache_read": True, "geometry": geometry,
            "editable_driver_bindings": bindings, "typed_archive_scope_word": job["scope"],
            "ordinary_saved_public_scope_is_unprojected": True, "saved_body_atom_id": output.FieldsValue["f140"],
            "saved_partition_marks": marks}


def auth_json(raw):
    planned = warm.FromData(json.loads(raw)["request"]["document"])
    creator, = planned.feature_timeline
    source = replace(planned, feature_timeline=(replace(creator, definition=ScopedExtrude(creator.definition, "first_creator", (), ())),))
    source.assert_valid()
    with TemporaryDirectory(prefix="kit-first-scope-authored-json-") as scratch:
        path = Path(scratch) / "authored.json"
        stream = BytesIO()
        result_path = write_document(source, path)
        result_stream = write_document(source, stream, destination_format=JSON_FORMAT)
        assert not result_path.dropped and not result_stream.dropped
        assert path.read_bytes() == stream.getvalue()
        assert open_document(path, strict=True).to_dict() == open_document(
            BytesIO(stream.getvalue()), source_format=JSON_FORMAT, strict=True).to_dict() == source.to_dict()
    return True


def worker(job):
    cold = warm.pinned(Path(job["cold_path"]), job["cold_input"]["sha256"], job["cold_input"]["bytes"])
    saved = warm.pinned(Path(job["saved_path"]), job["saved_proof"]["sha256"], job["saved_bytes"])
    warm.primed()
    for codec in ("utf-8", "utf-8-sig"):
        warm.lookup(codec)
    author_raw = warm.pinned(Path(job["authored_path"]), job["authored"]["sha256"], job["authored"]["bytes"])
    assert auth_json(author_raw)
    with no_runtime_io():
        document, payload, created = cold_read(cold, job)
        derivative = saved_read(saved, job)
    with TemporaryDirectory(prefix="kit-first-scope-json-") as scratch:
        target = Path(scratch) / "source.json"
        document.write_json(target)
        assert target.read_bytes() == payload and open_document(target, strict=True).to_dict() == document.to_dict()
        document_path = Path(scratch) / "conversion.json"
        stream = BytesIO(b"unchanged")
        rejected(lambda: write_document(document, document_path), "native-only feature definitions")
        rejected(lambda: write_document(document, stream, destination_format=JSON_FORMAT), "native-only feature definitions")
        assert not document_path.exists() and stream.getvalue() == b"unchanged" and stream.tell() == 0
    return {"cold": created, "native_saved": derivative, "in_memory_sdk_runtime_reads": 0, "strict_json_path_exact": True,
            "original_native_only_conversion_refusal": True, "authored_neutral_registry_json_path_stream_exact": True}


def capture(packet):
    observed = json.loads(warm.pinned(warm.ROOT / AUTHORITY, AUTHORITY_SHA))
    inputs = json.loads(warm.pinned(packet / "Packet.json", observed["packet_sha256"]))
    native = json.loads(warm.pinned(packet / "Native/Result.json", observed["raw_direct_observer_sha256"]))
    assert native["all_native_lifecycles_passed"] and native["controls_healthy"] and native["packet_inputs_unchanged"]
    assert observed["distinct_native_processes"] == 16 and observed["healthy_controls"] == 4
    assert native["packet_sha256"] == observed["packet_sha256"] and not observed["heldout_inputs_read"]
    outcomes = {}
    for case, group in inputs["cases"].items():
        build = group["proof"]
        points = json.loads(warm.pinned(packet / build["path"], build["sha256"], build["bytes"]))["vertices_m"]
        for mode, sample in group["modes"].items():
            role = f"{case}/{mode}"
            witness = observed["typed_saved_reports"][role]
            access = observed["native_selection_access"][role]
            edit, reopen = (native["phases"][role + stage] for stage in ("/Edit", "/Reopen"))
            native_saved = native["derivatives"][role]
            assert all(row["passed"] for row in (edit, reopen, witness))
            assert witness["sha256"] == access["input_sha256"] == edit["derivative_sha256"] == reopen["input_sha256"] == native_saved["sha256"]
            assert access["released"] and access["rollback_body_count"] == 0 and access["immutable"]
            assert access["accessed"]["feature_scope"]["value"] == bool(sample["scope_word"])
            assert access["accessed"]["body_count"]["value"] == 0
            assert access["direct"]["body_count"]["raw_value"] == -1
            assert not sample["scope_word"] or (access["accessed"]["array_count"] is None and access["accessed"]["auto_select"]["value"] is False)
            request = {"scope": sample["scope_word"], "profile": group["profile"], "labels": group["label_xyz_m"],
                       "label_routing": group["label_routing"], "points_mm": [[value * 1000 for value in point] for point in points],
                       "authored": group["request"], "authored_path": str(packet / group["request"]["path"]),
                       "initial": edit["states"]["Initial"], "reopened": reopen["states"]["Rebuilt"], "saved_proof": witness,
                       "cold_path": str(packet / sample["input"]["path"]), "cold_input": sample["input"],
                       "saved_path": str(packet / native_saved["path"]), "saved_bytes": native_saved["bytes"]}
            result = run((sys.executable, "-I", "-B", str(HERE), "--worker"), input=json.dumps(request), capture_output=True,
                         text=True, timeout=120)
            if result.returncode or result.stderr:
                raise ValueError(f"{role}: SDK process failed\n{result.stderr}")
            outcomes[role] = json.loads(result.stdout)
        same_modes = [outcomes[f"{case}/{mode}"]["cold"] for mode in ("All", "Selected")]
        assert len({row["portable_pair_model_sha256"] for row in same_modes}) == 1
    return {"schema": "kit.sw2026.first-creator-scope-sdk-read.v1", "baseline_revision": BASIS,
            "native_authority_sha256": AUTHORITY_SHA, "exact_build": observed["build"], "native_packet_sha256": observed["packet_sha256"],
            "native_terminal_sha256": observed["raw_direct_observer_sha256"], "saved_typed_result_sha256": observed["saved_typed_result_sha256"],
            "source_sha256": {name: warm.digest((warm.ROOT / name).read_bytes()) for name in SOURCES},
            "previous_native_processes": observed["distinct_native_processes"], "previous_native_controls": observed["healthy_controls"],
            "independent_sdk_processes": len(outcomes), "cases": outcomes, "new_native_processes": 0,
            "protected_sources_opened": 0, "public_writer_qualified": False, "original_source_transfer": False}


if __name__ == "__main__":
    if sys.argv[1:] == ["--worker"]:
        print(json.dumps(worker(json.load(sys.stdin)), sort_keys=True, allow_nan=False))
    else:
        parser = ArgumentParser(description="Replay bounded public first-creator scope for exact disclosed inputs")
        parser.add_argument("packet", type=Path)
        parser.add_argument("--output", required=True, type=Path)
        args = parser.parse_args()
        data = (json.dumps(capture(args.packet), indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
        with args.output.open("xb") as file:
            file.write(data)
        print(warm.digest(data))
