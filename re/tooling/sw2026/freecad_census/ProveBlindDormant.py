from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from json import dumps, loads
from pathlib import Path
from subprocess import check_output, run
import sys
from tarfile import open as open_tar
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
TOOLS = HERE.parents[1]
MEASUREMENTS = ROOT / "re/solidworks/measurements/2026"
BASE = "43b419d5c2d5a4a90731c26f90a87eafaa1012bc"
BASE_TREE = "533fbd624b08bbcb9454a815f27cc21532a158da"
CASE = "C130-P01"
CUSTODY = "1de42ebe8bf52b8403de2e6a73fe45b45ac83484a6532230d4b379aff93ca03f"
SOURCE = "d1f9225bfdf31d9708fc8fc8f94261edc9479d01d6a09c720ae70c16a5aa2362"
NATIVE = "e6d29c63227a56ab090d1243fc15a093ef1ec225042258376d6a0e3f838b0582"
CIRCLES = "4e3e6fc38ca158f18490f48416fd0dddae3627b36e99c7673a316193a9c2d427"
EQUATION = "90d9d22d737bd8d313a68d10eef1e3cb730bdae81c973a3656b591d627ad786b"
EQUATION_ARCHIVE = "5783b3944d76563ae8143b8789a923f1b07fb4eb94f4b59fef50b6b80ac696b6"
EPOCH = 1790000000
PRODUCTION = (
    "src/convert/adapters/solidworks/Archive/Construction/Blind/BlindEndInput.py",
    "src/convert/adapters/solidworks/Archive/Construction/Blind/SelectEndValue.py",
)


def digest(data):
    return sha256(data).hexdigest()


def wire(data):
    return (dumps(data, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def pinned(path, expected):
    raw = path.read_bytes()
    assert digest(raw) == expected, f"frozen input changed: {path.name}"
    return raw


def run_child(mode, sdk, request):
    child = run(
        (sys.executable, "-I", "-B", str(HERE), "--worker", mode, "--sdk", str(sdk)),
        input=wire(request),
        capture_output=True,
        timeout=120,
    )
    if child.returncode or child.stderr:
        sys.stderr.buffer.write(child.stderr)
        raise ValueError(f"guarded {mode} process failed")
    return loads(child.stdout)


def prepare_frozen_controls(equation_request, scratch):
    authored = scratch / "circle-requests"
    result = run(
        (sys.executable, "-I", "-B", str(TOOLS / "AuthorSdkCircleRequests.py"), str(authored)),
        capture_output=True,
        timeout=90,
        check=True,
    )
    assert result.stdout == b"6\n" and not result.stderr
    disclosed = loads(pinned(MEASUREMENTS / "AggregateCircleEndPort01.json", CIRCLES))
    circles = {}
    for row in disclosed["disclosed_cases"]:
        case = row["case"]
        circles[case] = loads(pinned(authored / (case + ".json"), row["authored_request_sha256"]))
    equation = loads(pinned(equation_request, EQUATION))
    return {"circles": circles, "equation": equation}, disclosed


def check_native_domain():
    native = loads(pinned(MEASUREMENTS / "GeneratedNestedAssemblySavedState01.json", NATIVE))
    assert native["typed_audit_passed"] and native["stream_round_trips"] == 36
    before, edited = (
        native["documents"][case]["plate"]["end_spec"]
        for case in ("FrozenGenerated", "GeneratedInput")
    )
    for value in (before, edited):
        assert (value["directions"], value["condition"], value["reverse"]) == (1, 0, 0)
    assert before["active_depth_m"] == before["inactive_depth_m"] == edited["inactive_depth_m"]
    assert edited["active_depth_m"] != edited["inactive_depth_m"]
    return {"receipt_sha256": NATIVE, "original": before, "native_saved_edit": edited}


def output_fingerprint(part):
    end = part.BossValue.EndValue.FieldsValue
    return {
        "archive_sha256": digest(part.BytesValue),
        "length": len(part.BytesValue),
        "streams": {key: digest(value) for key, value in sorted(part.StreamsValue.items())},
        "mode": [end["f08"], end["f0c"], end["f8c"]],
        "depths_m": [
            dim.ParameterValue.FieldsValue["f58"] for dim in part.BossValue.DimensionsValue[:2]
        ],
    }


def guarded_controls(sdk, request):
    sys.path[:0] = [str(sdk), str(TOOLS), str(TOOLS / "equations")]
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Core.Preparation.Circle.PrepareCircle import PrepareCircle
    from convert.adapters.solidworks.Core.Preparation.Equations.PrepareEqPart import PrepareEqPart
    from interchange.serialization.Deserialize import FromData
    from BuildSdkWidthDepth import author_document
    from CheckScopedPlainWriter import WriterAudit
    from ProveCircleEndPort import preload

    equation = request["equation"]
    source = author_document(equation)
    roots = {
        name: (FromData(data["document"]), data["created_at"])
        for name, data in request["circles"].items()
    }
    preload()
    guard = WriterAudit(sdk, Path("unused.SLDPRT"))
    sys.addaudithook(guard.observe)
    guard.phase = "prepare"
    try:
        first = PrepareEqPart(
            source,
            BytesIO(),
            equation["sdk_created_at"],
            WriteOptions(values={"final_destination": equation["settings"]["output"]["path_name"]}),
        )
        observations = {"equation": output_fingerprint(first)}
        for name, (document, epoch) in roots.items():
            locator = "C:\\KitSdkCandidates\\" + document.metadata["name"] + ".SLDPRT"
            part = PrepareCircle(
                document,
                BytesIO(),
                epoch,
                WriteOptions(values={"final_destination": locator}),
                Measured=True,
            )
            observations[name] = output_fingerprint(part)
    finally:
        guard.phase = "done"
    assert not guard.denied and not guard.target_opens
    return observations


def graph_part(intent, use_dormant):
    from convert.adapters.solidworks.Archive.Construction.Blind.ReadEndParam import ReadEndParam
    from convert.adapters.solidworks.Archive.Construction.Blind.BlindEndInput import BlindEndInput
    from ProveFcstdCorner import (
        BindWidthMut,
        MakeBlindMut,
        MakeCornerMut,
        MakePartBaseMut,
        MakePartProfMut,
        MakePartRecipe,
        MakeRectDimsMut,
        PersistentIds,
        ReadNodeName,
        RectDimInput,
        SelectBlindEnd,
    )

    recipe = intent.recipe
    settings = MakePartRecipe(recipe, EPOCH)
    allocator = PersistentIds()
    system = MakePartBaseMut(settings, recipe, allocator)
    profile = MakePartProfMut(system, settings, recipe, allocator)
    margin = min(recipe.WidthValue, recipe.HeightValue) / 4
    width, _ = MakeRectDimsMut(
        profile,
        RectDimInput(
            (recipe.WidthValue / 2, -margin),
            (recipe.WidthValue + margin, recipe.HeightValue / 2),
            settings.DesignIntent,
            settings.SelectedLeader,
            False,
        ),
        allocator,
        recipe.SketchDriverNames,
    )
    corner = MakeCornerMut(profile, system.OriginValue)
    assert (
        corner.SelectionValue.FieldsValue["f0f8"].FieldsValue["_point"]
        is system.OriginValue.PointValue
    )

    inputs = SelectBlindEnd(recipe, None, None)
    assert type(inputs) is BlindEndInput
    if use_dormant is not None:
        inputs = replace(inputs, DormantDepth=use_dormant)
    boss = MakeBlindMut(
        recipe.FeatureName,
        system.RootValue,
        profile,
        inputs,
        settings.TargetValue,
        allocator,
        settings.DesignIntent,
        settings.SelectedLeader,
    )
    active, dormant = boss.DimensionsValue[:2]
    BindWidthMut(system.RootValue, width, active)

    end = boss.EndValue.FieldsValue
    assert (end["f08"], end["f0c"], end["f8c"]) == (1, 0, 0)
    assert end["f18"] is active.DisplayValue and end["f20"] is dormant.DisplayValue
    assert ReadEndParam(inputs, end["f18"], 1) is active.DimensionValue
    assert ReadEndParam(inputs, end["f20"], 2) is dormant.DimensionValue
    assert active.ParameterValue is not dormant.ParameterValue
    assert dormant.ParameterValue.FieldsValue["owner"] is boss.FeatureValue
    assert active.ParameterValue.FieldsValue["owner"] is boss.FeatureValue

    (equation,) = system.RootValue.FieldsValue["f9d0"].FieldsValue["f58"]["items"]
    relation = equation["o"].FieldsValue
    left, right = (relation[side].FieldsValue["f10"]["items"] for side in ("f58", "f60"))
    for side, actual in ((left[0], active), (right[1], width)):
        wrapper = side["o"].FieldsValue["f80"].FieldsValue
        reference = wrapper["f58"].FieldsValue
        live = actual.HandleValue.FieldsValue
        assert reference["owner"] is live["owner"]
        assert reference["f4c"] == live["f4c"]
        assert reference["f58"].FieldsValue["owner"] is system.RootValue
        assert wrapper["fb0"] == actual.ParameterValue.FieldsValue["f58"]
    assert (
        relation["f10"]
        == f'"{recipe.DepthName}@{recipe.FeatureName}" = "{recipe.SketchDriverNames[0]}@{recipe.SketchName}" / 2'
    )
    return {
        "mode": [end["f08"], end["f0c"], end["f8c"]],
        "owners": [ReadNodeName(item.ParameterValue) for item in (active, dormant)],
        "dimension_ids": [item.DimensionValue.FieldsValue["f50"] for item in (active, dormant)],
        "equation": relation["f10"],
        "values_m": [item.ParameterValue.FieldsValue["f58"] for item in (active, dormant)],
    }


def validate_refusals():
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Archive.Construction.Blind.BlindEndInput import BlindEndInput
    from convert.adapters.solidworks.Archive.Construction.Blind.BossEndInput import BossEndInput
    from convert.adapters.solidworks.Core.Preparation.CheckPartOpts import CheckPartOpts
    from CheckScopedPlainWriter import reject

    invalid = {
        "zero": 0.0,
        "negative": -0.001,
        "nan": float("nan"),
        "infinity": float("inf"),
        "too_small": 1e-15,
        "boolean": True,
        "text": "0.01",
    }
    reasons = {}
    for label, value in invalid.items():
        kind = TypeError if label in ("boolean", "text") else ValueError
        reason = "real numeric input" if kind is TypeError else "finite and at least 1e-14 metres"
        reasons[label] = reject(
            lambda: BlindEndInput(0.02, False, 19000, DormantDepth=value), kind, reason
        )
    reasons["reversed_end"] = reject(
        lambda: BlindEndInput(0.02, True, 19000, DormantDepth=0.01),
        ValueError,
        "requires the forward direction",
    )
    reasons["active_mode"] = reject(
        lambda: BossEndInput(
            0.02, False, 19000, "two_directions", SecondDepth=0.01, DormantDepth=0.01
        ),
        TypeError,
        "unexpected keyword argument",
    )
    reasons["enable_second_in_blind_mode"] = reject(
        lambda: BossEndInput(0.02, False, 19000, "blind", SecondDepth=0.01),
        ValueError,
        "exactly its active second depth",
    )
    reasons["public_write_option"] = reject(
        lambda: CheckPartOpts(WriteOptions(values={"dormant_depth": 0.01})),
        ValueError,
        "unsupported plain part preparation options",
    )
    return reasons


def guarded_source(request):
    sys.path[:0] = [str(ROOT / "src"), str(TOOLS), str(HERE.parent)]
    from convert import open_document, write_document
    from convert.adapters.registry.RegistryErrors import NotFoundError
    from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLength import ReadLength
    from CheckScopedPlainWriter import WriterAudit, reject
    from PlanFcstdCorner import plan_corner
    from VerifyLocalSketchExpr import guard_source
    from ProveFcstdCorner import prewarm

    path = Path(request["source"]).resolve(strict=True)
    compact = "".join(character for character in str(path).casefold() if character.isalnum())
    assert not any(marker in compact for marker in ("heldout", "holdout", "sealed"))
    assert path.suffix.casefold() == ".fcstd"
    pinned(path, SOURCE)
    reads, denied = guard_source(path, ROOT / "src")
    document = open_document(
        path,
        source_format="freecad.fcstd",
        strict=True,
        include_brep=True,
        include_tessellation=True,
    )
    document.assert_valid()
    assert document.source.sha256 == SOURCE and reads and not denied
    consumed = len(reads)
    prewarm()
    before = document.to_json(indent=None)
    sentinel = b"unchanged output"
    sink = BytesIO(sentinel)
    sink.seek(3)
    guard = WriterAudit(ROOT / "src", Path("unused.SLDPRT"))
    sys.addaudithook(guard.observe)
    guard.phase = "prepare"
    try:
        intent = plan_corner(document, CASE)
        (feature,) = document.feature_timeline
        (dormant,) = (
            param
            for param in document.parameters
            if param.owner_id == feature.id
            and param.id in feature.parameter_ids
            and param.attributes.get("freecad_path") == "Length2"
        )
        assert dormant.value == feature.definition.second_length and dormant.expression is None
        assert feature.definition.second_end_condition is None
        default = graph_part(intent, None)
        requested = graph_part(intent, ReadLength(dormant.value))
        default_values = default.pop("values_m")
        requested_values = requested.pop("values_m")
        assert default == requested
        assert default_values == [intent.recipe.DepthValue, intent.recipe.DepthValue]
        assert requested_values == [intent.recipe.DepthValue, ReadLength(dormant.value)]
        assert requested_values[0] != requested_values[1]
        negatives = validate_refusals()
        public = reject(
            lambda: write_document(
                document,
                sink,
                destination_format="solidworks.sldprt",
                allow_carrier=False,
                values={"require_native_transfers": True},
            ),
            NotFoundError,
            "does not support the destination",
        )
        assert document.to_json(indent=None) == before
    finally:
        guard.phase = "done"
    assert not denied and not guard.denied and not guard.target_opens and len(reads) == consumed
    assert sink.getvalue() == sentinel and sink.tell() == 3
    pinned(path, SOURCE)
    return {
        "source_sha256": SOURCE,
        "dormant_parameter_id": dormant.id,
        "archive_graph": requested,
        "default_active_dormant_m": default_values,
        "explicit_active_dormant_m": requested_values,
        "refusals": negatives,
        "intact_public_refusal": public,
        "runtime_data_reads": 0,
    }


def verify_controls(result, disclosed):
    assert result["equation"]["archive_sha256"] == EQUATION_ARCHIVE
    for row in disclosed["disclosed_cases"]:
        observed = result[row["case"]]
        assert observed["archive_sha256"] == row["archive_sha256"]
        assert observed["streams"] == row["streams"]
        if row["case"] in ("two-front", "two-rev-top"):
            assert observed["mode"][0] == 0
            assert observed["depths_m"][0] != observed["depths_m"][1]


def measure(inventory, equation_request):
    sources = {path: digest((ROOT / path).read_bytes()) for path in PRODUCTION}
    method = digest(HERE.read_bytes())
    source_rows = loads(pinned(inventory, CUSTODY))
    (row,) = (item for item in source_rows["files"] if item["case_id"] == CASE)
    assert row["sha256"] == SOURCE
    assert (
        check_output(("git", "rev-parse", BASE + ":src"), cwd=ROOT, text=True).strip() == BASE_TREE
    )
    native = check_native_domain()
    with TemporaryDirectory(prefix="KitBlindDormant.") as workspace:
        scratch = Path(workspace)
        export = scratch / "base"
        export.mkdir()
        archive = check_output(("git", "archive", BASE, "src"), cwd=ROOT)
        with open_tar(fileobj=BytesIO(archive), mode="r:") as stream:
            stream.extractall(export, filter="data")
        requests, disclosed = prepare_frozen_controls(equation_request, scratch)
        previous = run_child("controls", export / "src", requests)
        current = run_child("controls", ROOT / "src", requests)
        assert current == previous, "legacy complete archives or their owned end fields changed"
        verify_controls(current, disclosed)
    proof = run_child("source", ROOT / "src", {"source": row["source_path"]})
    assert proof == run_child("source", ROOT / "src", {"source": row["source_path"]})
    assert digest(HERE.read_bytes()) == method
    assert sources == {path: digest((ROOT / path).read_bytes()) for path in PRODUCTION}
    return {
        "schema": "kit.sw2026.blind-dormant-depth.v1",
        "base_revision": BASE,
        "base_src_tree": BASE_TREE,
        "method_sha256": method,
        "production_sha256": sources,
        "native_domain_evidence": native,
        "c130_model_graph": proof,
        "default_exact_controls": current,
        "fresh_guarded_processes": 4,
        "legacy_exact_complete_archives": len(current),
        "native_launches": 0,
        "runtime_data_reads": 0,
        "fcstd_outputs": 0,
        "corpus_credit": 0,
    }


def main():
    if sys.flags.optimize:
        raise ValueError("run with proof assertions enabled")
    parser = ArgumentParser()
    parser.add_argument("--worker", choices=("controls", "source"))
    parser.add_argument("--sdk", type=Path)
    parser.add_argument("--inventory", type=Path)
    parser.add_argument("--equation-request", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        request = loads(sys.stdin.buffer.read())
        proof = (
            guarded_controls(args.sdk, request)
            if args.worker == "controls"
            else guarded_source(request)
        )
        sys.stdout.buffer.write(wire(proof))
        return
    if args.inventory is None or args.equation_request is None or args.output is None:
        parser.error("--inventory, --equation-request and --output are required")
    raw = wire(measure(args.inventory, args.equation_request))
    with args.output.open("xb") as stream:
        stream.write(raw)
    print(digest(raw))


if __name__ == "__main__":
    main()
