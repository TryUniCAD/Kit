from argparse import ArgumentParser
from contextlib import contextmanager
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from math import isclose
from pathlib import Path
from subprocess import check_output, run
from tarfile import open as open_tar
from tempfile import TemporaryDirectory
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
BASIS = "839d77474155c30a37978788ee2296d18036b328"
AUTHORITY = "90d4d1836492f49fd2d6c99a122664c5be918d128dcd1c604a589d2ea724fa21"
PREVIOUS = "0865fd5d0c9c9602f22b4494498f69a6962fa4b997564dc88677825c703dea65"
PART_FORMAT = "solidworks.sldprt"
JSON_FORMAT = "interchange.json"


def wire(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(raw):
    return sha256(raw).hexdigest()


def pinned(path, identity, length=None):
    assert path.is_file() and not path.is_symlink()
    raw = path.read_bytes()
    assert digest(raw) == identity and (length is None or len(raw) == length)
    return raw


def summary(document):
    return {"document_sha256": digest(wire(document.to_dict())), "solid_count": len(document.bodies),
            "timeline": [[row.id, str(row.operation), type(row.definition).__name__] for row in document.feature_timeline
                         if row.kind.value == "extrusion"]}


def baseline(job, sdk):
    sys.path.insert(0, str(Path(sdk) / "src"))
    from convert import open_document

    raw = pinned(Path(job["path"]), job["sha256"], job.get("bytes"))
    return {name: summary(open_document(BytesIO(raw), source_format=PART_FORMAT, strict=True, include_brep=include))
            for name, include in (("complete", True), ("metadata_only", False))}


@contextmanager
def changed_field(fields, name, value):
    old = fields[name]
    fields[name] = value
    try:
        yield
    finally:
        fields[name] = old


def before_scope(document, creator):
    from convert.adapters.solidworks.Core.Adapter import KSourceSemanticShaTwoFive, SemanticShaTwo
    from interchange.Core.Common import FreezeMapping
    from interchange.Enums.EnumFeatures import BooleanOp
    from interchange.Features.ScopedExtrude import ScopedExtrude

    assert isinstance(creator.definition, ScopedExtrude)
    prior = replace(creator, operation=BooleanOp.KJoin, definition=creator.definition.Extrusion)
    ordinary = replace(document, feature_timeline=tuple(prior if row is creator else row for row in document.feature_timeline))
    assert document.metadata[KSourceSemanticShaTwoFive] == SemanticShaTwo(document)
    prior_digest = SemanticShaTwo(ordinary)
    assert document.metadata[KSourceSemanticShaTwoFive] != prior_digest
    return replace(ordinary, metadata=FreezeMapping({**ordinary.metadata, KSourceSemanticShaTwoFive: prior_digest}))


def physical_owners(ordinary, raw, prior):
    import MeasureWarmNestedLeaf as warm

    archive = warm.SldprtArchive.from_bytes(raw)
    payloads, _, marks = warm.ReadBodyKernel(archive.require(warm.PARTITION), warm.PARTITION)
    kernel = warm.DecodeBrepModel(payloads[0].data)
    assert kernel is not None
    before = replace(ordinary, brep=kernel)
    graph = warm.ReadNamedBody(before, archive, 0)
    assert graph.MarksValue == marks and warm.BindBodyName(before, graph) == ordinary
    link = graph.LinkValue
    features = warm.IndexFeatures(link)
    creator = features[graph.FeatureId]
    owner = warm.ReadExtrude(link, creator, features)
    primary, inactive, draft, draft_second = (owner.EndValue.FieldsValue[name] for name in ("f18", "f20", "fc8", "fd0"))
    assert len({primary, inactive, draft, draft_second}) == 4
    assert creator.FieldsValue["f544"] == prior["stored_existing_body_scope"]
    assert creator.FieldsValue["has_f548"] == creator.FieldsValue["has_f530"] == 0
    assert creator.FieldsValue.get("f548") is None and creator.FieldsValue.get("f530") is None
    assert graph.AtomValue.FieldsValue["f140"] == prior["actual_sole_body_atom_id"]
    assert list(marks) == prior["typed_marks"]
    assert owner.RequireDepth().DepthValue.native_value == prior["typed_depth_m"]
    warm.CheckThinMarks(link.ConfigValue.RootValue, creator, marks)
    return archive, graph, owner


def changed_cases(ordinary, archive, graph, owner):
    import MeasureColdCreatorScope as cold
    import MeasureWarmNestedLeaf as warm
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.SavedScope.WithSavedScope import ReadSaveScope

    def reject_graph(candidate, expected, document=ordinary):
        return cold.rejected(lambda: ReadSaveScope(document, archive, candidate), expected)

    def reject_field(fields, name, value, expected):
        with changed_field(fields, name, value):
            return reject_graph(graph, expected)

    assert graph.MarksValue is not None
    ghost = graph.LinkValue.ConfigValue.RootValue.FieldsValue["fd90"]
    scope = owner.NodeValue.FieldsValue
    chooser = scope["f4b0"]
    ends = owner.EndValue.FieldsValue
    chain = owner.ProfileValue.FieldsValue["d5c0"]["f2a8"][0]["chain"]
    members = chain.FieldsValue["f08"]
    header = graph.LinkValue.ConfigValue.HeaderValue.FieldsValue["f38"].FieldsValue
    profile = owner.ProfileValue.FieldsValue
    (configuration,) = ordinary.configurations
    controls = {
        "detached_atom": reject_graph(replace(graph, AtomValue=replace(graph.AtomValue)), "alternate body state"),
        "wrong_rollback": reject_graph(replace(graph, MarksValue=(graph.MarksValue[0] + 1, graph.MarksValue[1])),
                                       "rollback marks differ"),
        "ghost_body": reject_field(ghost, "n", 1, "unresolved live or ghost body identities"),
        "selected_wrapper": reject_field(scope, "has_f548", 1, "alternate output or modifier state"),
        "extra_chooser": reject_field(chooser, "f48", {"n": 1, "items": [{"o": owner.ProfileValue}]},
                                      "additional chooser input"),
        "aliased_inactive_depth": reject_field(ends, "f20", ends["f18"], "end roles share live owners"),
        "reversed": reject_field(ends, "f8c", 1, "requires one ordinary forward blind profile"),
        "wrong_chain": reject_field(members, "items", [{"v": number} for number in (1, 2, 2, 4)],
                                    "contour differs from its live profile"),
        "different_header_part": reject_field(header, "file", replace(header["file"], PathValue="C:\\wrong.SLDPRT"),
                                               "actual saved part and configuration"),
        "inactive_configuration": reject_graph(graph, "complete active configuration",
                                               replace(ordinary, configurations=(replace(configuration, active=False),))),
        "different_configuration": reject_graph(graph, "does not own selected Config-0",
                                                replace(ordinary, configurations=(replace(configuration, name="not its actual row"),))),
    }
    assert ReadSaveScope(ordinary, archive, graph).feature_timeline[-1].definition.ScopeMode == "first_creator"
    assert warm.NativeNodeId(owner.NodeValue) == graph.FeatureId and profile["d5c0"]["f2a8"][0]["chain"] is chain
    return controls


def verify_derivative(document, raw, job):
    import MeasureColdCreatorScope as cold
    from convert import open_document
    from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismParam import ReadPrismParam
    from interchange.Features.ScopedExtrude import ScopedExtrude

    body, creator = cold.body_and_step(document)
    selected = bool(job["scope"])
    assert isinstance(creator.definition, ScopedExtrude) == selected
    if selected:
        assert creator.operation.value == "create" and creator.definition.ScopeMode == "first_creator"
        assert creator.definition.SelectedBodyIds == creator.definition.AffectedBodyIds == ()
        ordinary = before_scope(document, creator)
    else:
        assert creator.operation.value == "join"
        ordinary = document
    assert summary(ordinary) == job["old"]["complete"]
    state, prior = job["native_state"], job["typed"]
    depth, bindings = cold.verify_drivers(document, creator, state, prior)
    geometry = cold.verify_geometry(document, body, job["points_mm"], depth, state)
    assert wire(geometry) == wire(job["cold_receipt"]["geometry"])
    assert bindings == job["cold_receipt"]["editable_driver_bindings"]
    assert cold.warm.observe(raw, job["profile"])["height"]["text_m"] == prior["stored_label_xyz_m"][1]
    archive, graph, owner = physical_owners(ordinary, raw, prior)
    inactive = ReadPrismParam(owner.EndValue.FieldsValue["f20"], False)[2]
    assert isclose(inactive, job["initial_depth_m"], rel_tol=1e-12) and inactive != depth.value.value / 1000
    chain = owner.ProfileValue.FieldsValue["d5c0"]["f2a8"][0]["chain"]
    controls = changed_cases(ordinary, archive, graph, owner) if selected else {}
    payload = (document.to_json() + "\n").encode()
    assert open_document(BytesIO(payload), source_format=JSON_FORMAT, strict=True).to_dict() == document.to_dict()
    return payload, {"operation": str(creator.operation), "scope": "first_creator" if selected else None,
                     "configuration": document.configurations[0].name, "native_feature_id": graph.FeatureId,
                     "native_profile_id": prior["typed_profile_id"], "actual_atom_id": graph.AtomValue.FieldsValue["f140"],
                     "body_match_tag": graph.AtomValue.FieldsValue["f180"], "actual_marks": graph.MarksValue,
                     "live_depth_mm": depth.value.value, "inactive_stored_depth_mm": inactive * 1000,
                     "live_driver_bindings": bindings, "saved_geometry": geometry, "strict_json_stream_exact": True,
                     "actual_contour_links": [row["v"] for row in chain.FieldsValue["f08"]["items"]],
                     "payloads": {entry.kind: entry.sha256 for entry in document.brep_payloads},
                     "only_creator_and_dependent_semantic_digest_changed": selected, "negative_contrasts": controls}


def worker(job):
    sys.path.insert(0, str(HERE.parent))
    import MeasureColdCreatorScope as cold
    from convert import open_document

    raw = pinned(Path(job["path"]), job["sha256"], job.get("bytes"))
    authored = job["authored"]
    warm = cold.warm
    warm.primed()
    for encoding in ("utf-8", "utf-8-sig"):
        warm.lookup(encoding)
    assert cold.auth_json(pinned(Path(authored["path"]), authored["sha256"], authored["bytes"]))
    with cold.no_runtime_io():
        document = open_document(BytesIO(raw), source_format=PART_FORMAT, strict=True)
        metadata = open_document(BytesIO(raw), source_format=PART_FORMAT, strict=True, include_brep=False)
        assert summary(metadata) == job["old"]["metadata_only"]
        if "typed" in job:
            payload, proof = verify_derivative(document, raw, job)
        else:
            assert summary(document) == job["old"]["complete"]
            payload, proof = None, {"complete_public_read_unchanged": True, **summary(document)}
    if payload is not None:
        with TemporaryDirectory(prefix="kit-saved-scope-json-") as scratch:
            target = Path(scratch) / "document.json"
            document.write_json(target)
            assert target.read_bytes() == payload and open_document(target, strict=True).to_dict() == document.to_dict()
    return {"sha256": job["sha256"], "sdk_runtime_input_reads": 0, "metadata_only_unchanged": True,
            "strict_json_path_exact": payload is not None, **proof}


def invoke(job, *options):
    result = run((sys.executable, "-I", "-B", str(HERE), *options), input=json.dumps(job), text=True,
                 capture_output=True, timeout=120)
    if result.returncode or result.stderr:
        raise ValueError(f"{job['role']}: isolated SDK worker failed\n{result.stderr}")
    return json.loads(result.stdout)


def exact_inputs(packet, multi):
    receipts = ROOT / "re/solidworks/measurements/2026"
    authority = json.loads(pinned(receipts / "FirstCreatorScopeAcceptance01.json", AUTHORITY))
    previous = json.loads(pinned(receipts / "SdkColdFirstCreatorScopeRead01.json", PREVIOUS))
    plan = json.loads(pinned(packet / "Packet.json", authority["packet_sha256"]))
    native = json.loads(pinned(packet / "Native/Result.json", authority["raw_direct_observer_sha256"]))
    assert authority["healthy_controls"] == 4 and authority["distinct_native_processes"] == 16
    assert native["all_native_lifecycles_passed"] and native["controls_healthy"] and native["packet_inputs_unchanged"]
    assert not authority["heldout_inputs_read"] and not previous["protected_sources_opened"]
    for role, row in native["derivatives"].items():
        group_name, mode = role.split("/")
        group = plan["cases"][group_name]
        proof = authority["typed_saved_reports"][role]
        access = authority["native_selection_access"][role]
        reopened = native["phases"][role + "/Reopen"]
        edit = native["phases"][role + "/Edit"]
        assert proof["passed"] and reopened["passed"] and edit["passed"] and access["immutable"]
        assert row["sha256"] == proof["sha256"] == reopened["input_sha256"] == edit["derivative_sha256"] == access["input_sha256"]
        assert access["rollback_body_count"] == 0 and access["accessed"]["body_count"]["value"] == 0
        record = group["proof"]
        points = json.loads(pinned(packet / record["path"], record["sha256"], record["bytes"]))["vertices_m"]
        yield {"role": role, **row, "path": str(packet / row["path"]), "typed": proof,
               "cold_receipt": previous["cases"][role]["native_saved"], "scope": group["modes"][mode]["scope_word"],
               "initial_depth_m": group["dimensions_m"][2], "profile": group["profile"],
               "native_state": reopened["states"]["Rebuilt"], "points_mm": [[1000 * value for value in point] for point in points],
               "authored": {**group["request"], "path": str(packet / group["request"]["path"])}}
    for group_name, group in plan["cases"].items():
        authored = {**group["request"], "path": str(packet / group["request"]["path"])}
        for mode, entry in group["modes"].items():
            row = entry["input"]
            assert row["sha256"] == previous["cases"][f"{group_name}/{mode}"]["cold"]["sha256"]
            yield {"role": f"{group_name}/{mode}/Cold", **row, "path": str(packet / row["path"]), "authored": authored}
    control = plan["cases"]["Single"]["request"]
    authored = {**control, "path": str(packet / control["path"])}
    yield {"role": "L1 saved contrast", "path": str(ROOT / "re/solidworks/v2026/corpus/ladder/L1_boss.SLDPRT"),
           "sha256": "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6", "authored": authored}
    yield {"role": "explicit multi-stock contrast", "path": str(multi),
           "sha256": "748cdbec3fe61d6801f3d606e64fe42ecba95e9a647897be3fe3790570a889f3", "authored": authored}


def capture(packet, multi):
    typed = "Core/TypedResolved"
    files = (
        "Core/Adapter.py",
        *(f"{typed}/BodyNames/{name}.py" for name in ("BodyNameGraph", "WithBodyNames", "ReadNamedBody",
                                                     "ReadBodyCache", "Revolves/ReadRevolveBody")),
        *(f"{typed}/Geometry/{name}.py" for name in ("CheckPrismEnd", "CheckPrismProf", "ReadPrismLoop", "ColdOutput/BindPrismCreate")),
        *(f"{typed}/Revolves/{name}.py" for name in ("SelectedCut/ReadRevChoices", "SelectedCut/ReadRevFace", "SelectedCut/CheckRevSelf",
                                                    "Thin/Saved/CheckThinMarks", "Thin/Saved/CheckThinState")),
        f"{typed}/Equations/CheckEqConfig.py",
    )
    adapter = ROOT / "src/convert/adapters/solidworks"
    dependencies = [*(adapter / name for name in files), *sorted((adapter / "Core/TypedResolved/Geometry/SavedScope").glob("*.py")),
                    HERE, HERE.with_name("MeasureColdCreatorScope.py"), HERE.with_name("MeasureWarmNestedLeaf.py")]
    with TemporaryDirectory(prefix="kit-saved-scope-pinned-sdk-") as scratch:
        original = check_output(("git", "-C", str(ROOT), "archive", BASIS, "src"))
        with open_tar(fileobj=BytesIO(original)) as tree:
            tree.extractall(scratch, filter="data")
        cases = {}
        for job in exact_inputs(packet, multi):
            job["old"] = invoke(job, "--baseline", scratch)
            cases[job["role"]] = invoke(job, "--worker")
    return {"schema": "kit.sw2026.saved-first-creator-scope.v1", "baseline_revision": BASIS,
            "prior_native_authority_sha256": AUTHORITY, "prior_sdk_receipt_sha256": PREVIOUS,
            "dependencies_sha256": {file.relative_to(ROOT).as_posix(): digest(file.read_bytes()) for file in dependencies},
            "fresh_sdk_processes": 2 * len(cases), "cases": cases, "new_native_processes": 0, "heldout_inputs_read": 0,
            "full_source_transfer_qualified": False, "public_writer_qualified": False}


if __name__ == "__main__":
    if sys.argv[1:2] == ["--baseline"]:
        print(json.dumps(baseline(json.load(sys.stdin), sys.argv[2]), sort_keys=True, allow_nan=False))
    elif sys.argv[1:] == ["--worker"]:
        print(json.dumps(worker(json.load(sys.stdin)), sort_keys=True, allow_nan=False))
    else:
        parser = ArgumentParser(description="Compare only disclosed first-boss native-saved parts and existing controls")
        parser.add_argument("packet", type=Path)
        parser.add_argument("--multi-stock", type=Path, required=True)
        parser.add_argument("--output", type=Path, required=True)
        args = parser.parse_args()
        payload = (json.dumps(capture(args.packet, args.multi_stock), indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
        with args.output.open("xb") as target:
            target.write(payload)
        print(digest(payload))
