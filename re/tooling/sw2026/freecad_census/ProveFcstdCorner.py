from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from json import dumps, loads
from pathlib import Path
from subprocess import check_output, run
import sys

ROOT = Path(__file__).resolve().parents[4]
TOOLS = ROOT / "re/tooling/sw2026"
CENSUS = "1de42ebe8bf52b8403de2e6a73fe45b45ac83484a6532230d4b379aff93ca03f"
BASE = "ffa49a63caf2b3c433c05433c7b638e5d0d4fde7"
SHEET = "73cd885cd4755b274fe1106db3022923352ea45a7a4d9964d48202790a47de61"
SENTINEL = b"original caller data"


def sha(data):
    return sha256(data).hexdigest()


def wire(value):
    return (dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def install_paths():
    sys.path[:0] = [
        str(ROOT / "src"),
        str(TOOLS),
        str(TOOLS / "attached_top_box_source"),
        str(Path(__file__).resolve().parent),
    ]


def refuse(function, reason):
    try:
        function()
    except (ValueError, RuntimeError) as error:
        if reason in str(error):
            return {"exception": type(error).__name__, "reason": reason}
        raise ValueError(f"expected {reason!r}, received {type(error).__name__}") from error
    raise ValueError(f"unexpected passage at {reason!r}")


install_paths()

from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeBlindMut import MakeBlindMut
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import PersistentIds
from convert.adapters.solidworks.Archive.Construction.Part.Equations.BindWidthMut import (
    BindWidthMut,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartBaseMut import MakePartBaseMut
from convert.adapters.solidworks.Archive.Construction.Part.MakePartProfMut import MakePartProfMut
from convert.adapters.solidworks.Archive.Construction.Part.SelectBlindEnd import SelectBlindEnd
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.MakeCornerMut import (
    MakeCornerMut,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeRectDimsMut import (
    MakeRectDimsMut,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.ReadPointPair import (
    ReadPointPair,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RectDimInput import (
    RectDimInput,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe

from convert import open_document, write_document
from convert.adapters.solidworks.Core.Preparation.Equations.PlanEqPart import PlanEqPart
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from CheckScopedPlainWriter import WriterAudit
from FcstdRectangleOwners01 import rectangular_source_measure, topology_compare
from PlanFcstdCorner import plan_corner
from VerifyLocalSketchExpr import PINS, guard_source
from VerifyOriginalFcstdAttachedBox import prewarm


def build_owned_graph(intent):
    plan = intent.recipe
    written_at = 1790000000
    settings = MakePartRecipe(plan, written_at)
    allocator = PersistentIds()
    system = MakePartBaseMut(settings, plan, allocator)
    profile = MakePartProfMut(system, settings, plan, allocator)
    margin = min(plan.WidthValue, plan.HeightValue) / 4.0
    label = RectDimInput(
        (plan.WidthValue / 2, -margin),
        (plan.WidthValue + margin, plan.HeightValue / 2),
        settings.DesignIntent,
        settings.SelectedLeader,
        False,
    )
    width, height = MakeRectDimsMut(profile, label, allocator, plan.SketchDriverNames)
    origin = MakeCornerMut(profile, system.OriginValue)
    end = SelectBlindEnd(plan, None, None)
    boss = MakeBlindMut(
        plan.FeatureName,
        system.RootValue,
        profile,
        end,
        settings.TargetValue,
        allocator,
        settings.DesignIntent,
        settings.SelectedLeader,
    )
    live_depth, dormant_depth = boss.DimensionsValue[:2]
    end_fields = boss.EndValue.FieldsValue
    assert end_fields["f08"] == 1 and end_fields["f0c"] == 0 and not end_fields["f8c"]
    assert (
        end_fields["f18"] is live_depth.DisplayValue
        and end_fields["f20"] is dormant_depth.DisplayValue
    )
    assert dormant_depth.ParameterValue is not live_depth.ParameterValue
    assert dormant_depth.ParameterValue.FieldsValue["owner"] is boss.FeatureValue
    BindWidthMut(system.RootValue, width, live_depth)

    polygon = profile.GeometryValue
    points = polygon.PointValues
    assert tuple(map(ReadPointPair, points)) == plan.VerticesValue
    joins = {}
    for index, source_id in enumerate(intent.local_rule_ids):
        joint = (index + 1) % len(points)
        assert polygon.LineValues[index].FieldsValue["_end"] is points[joint]
        assert polygon.LineValues[joint].FieldsValue["_start"] is points[joint]
        joins[source_id] = joint
    dimensions = polygon.SketchValue.FieldsValue["dims"]
    axes = {}
    for index, (row, source_id) in enumerate(
        zip(dimensions["log_g1"], intent.axis_rule_ids, strict=True)
    ):
        node = row["d"]
        assert node["h1"].FieldsValue["_line"] is polygon.LineValues[index]
        assert node["f80"] == 4 + index % 2
        axes[source_id] = index
    assert len(dimensions["log_g2"]) == 1 and dimensions["log_g2"][0]["d"] is origin.RelationValue
    relation = origin.RelationValue
    assert relation["h2"].FieldsValue["_point"] is points[0]
    assert relation["h1"].FieldsValue["_point"] is origin.ExternalPoint is not points[0]
    assert (
        origin.SelectionValue.FieldsValue["f0f8"].FieldsValue["_point"]
        is system.OriginValue.PointValue
    )
    assert ReadPointPair(origin.ExternalPoint) == ReadPointPair(points[0]) == (0.0, 0.0)

    driver_rows = []
    for index, (driver, source_id) in enumerate(
        zip((width, height), intent.driver_rule_ids, strict=True)
    ):
        fields = driver.DimensionValue.FieldsValue
        operands = (fields["h1"].FieldsValue["_point"], fields["h2"].FieldsValue["_point"])
        assert operands[0] is points[index] and operands[1] is points[index + 1]
        assert driver.DimensionValue.ClassValue.NameValue == "sgPntPntDist"
        assert driver.ParameterValue.FieldsValue["owner"] is profile.ProfileValue
        assert (
            driver.ParameterValue.FieldsValue["f58"] == (plan.WidthValue, plan.HeightValue)[index]
        )
        driver_rows.append(
            {
                "rule": source_id,
                "parameter": intent.source_parameter_ids[index],
                "name": ReadNodeName(driver.ParameterValue),
                "points": [index, index + 1],
            }
        )
    assert live_depth.ParameterValue.FieldsValue["owner"] is boss.FeatureValue
    assert live_depth.ParameterValue.FieldsValue["f58"] == plan.DepthValue
    manager = system.RootValue.FieldsValue["f9d0"]
    (equation,) = manager.FieldsValue["f58"]["items"]
    relation_fields = equation["o"].FieldsValue
    left, right = (relation_fields[field].FieldsValue["f10"]["items"] for field in ("f58", "f60"))
    for token, actual in ((left[0]["o"], live_depth), (right[1]["o"], width)):
        wrapper = token.FieldsValue["f80"].FieldsValue
        clone = wrapper["f58"].FieldsValue
        live = actual.HandleValue.FieldsValue
        assert wrapper["fb0"] == actual.ParameterValue.FieldsValue["f58"]
        assert clone["f4c"] == live["f4c"]
        assert (
            clone["owner"] is live["owner"]
            and clone["f58"].FieldsValue["owner"] is system.RootValue
        )
    expected = f'"{plan.DepthName}@{plan.FeatureName}" = "{plan.SketchDriverNames[0]}@{plan.SketchName}" / 2'
    assert relation_fields["f10"] == expected
    return {
        "source_joins_to_shared_point": joins,
        "source_axis_rules_to_lines": axes,
        "source_root_rule": intent.origin_rule_id,
        "native_origin_handles_distinct": True,
        "sketch_drivers": driver_rows,
        "depth_driver": {
            "parameter": intent.source_parameter_ids[2],
            "name": ReadNodeName(live_depth.ParameterValue),
        },
        "live_equation": expected,
        "ordinary_dormant_driver": {
            "name": ReadNodeName(dormant_depth.ParameterValue),
            "value_mm": dormant_depth.ParameterValue.FieldsValue["f58"] * 1000,
        },
        "construction_event_for_graph_only": written_at,
    }


def run_case(request):
    expected = ({**PINS, "C059-P01": SHEET}).get(request["case_id"])
    assert expected is not None and request["sha256"] == expected
    source = Path(request["source"]).resolve(strict=True)
    compact = "".join(ch.lower() for ch in str(source) if ch.isalnum())
    assert source.suffix.casefold() == ".fcstd"
    assert not any(label in compact for label in ("sealed", "heldout", "holdout"))
    assert sha(source.read_bytes()) == request["sha256"]
    reads, denied = guard_source(source, ROOT / "src")
    document = open_document(
        source,
        source_format="freecad.fcstd",
        strict=True,
        include_brep=True,
        include_tessellation=True,
    )
    document.assert_valid()
    assert reads and not denied
    intake_reads = len(reads)
    assert document.source.sha256 == request["sha256"]
    original = document.to_json(indent=None)
    assert type(document).from_json(original) == document

    prewarm()
    target = BytesIO(SENTINEL)
    target.seek(3)
    guard = WriterAudit(ROOT / "src", source.with_suffix(".SLDPRT"))
    sys.addaudithook(guard.observe)
    guard.phase = "prepare"
    try:
        result = measure_case(document, request["case_id"], target)
        assert document.to_json(indent=None) == original
    finally:
        guard.phase = "done"
    assert not denied and not guard.denied and not guard.target_opens and len(reads) == intake_reads
    assert target.getvalue() == SENTINEL and target.tell() == 3
    assert sha(source.read_bytes()) == request["sha256"]
    return {
        "sha256": request["sha256"],
        "release": document.source.application_version,
        "full_neutral_sha256": sha(original.encode()),
        "input_byte_reads": intake_reads,
        "runtime_data_reads": 0,
        **result,
    }


def measure_case(document, case_id, target):
    if case_id == "C059-P01":
        return {
            "sheet_refusal": refuse(
                lambda: plan_corner(document, case_id),
                "the source needs one owned local width-to-depth equation",
            )
        }
    before = {
        "shared_equation_plan": refuse(lambda: PlanEqPart(document), "extended source state"),
        "normal_candidate_prepare": refuse(
            lambda: PrepareNative(document, "QualifiedCorner.SLDPRT", 1790000000),
            "bare local import",
        ),
        "public_stream": refuse(
            lambda: write_document(
                document,
                target,
                destination_format="solidworks.sldprt",
                allow_carrier=False,
                values={"require_native_transfers": True},
            ),
            "does not support the destination",
        ),
    }
    intent = plan_corner(document, case_id)
    graph = build_owned_graph(intent)
    (sketch,) = document.sketches
    (definition,) = document.feature_timeline
    (plane,) = (row for row in document.support_planes if row.id == intent.source_support_id)
    native = document.brep
    generated, volume, area, bounds = BuildPrism(
        intent.recipe.BodyId,
        plane.transform,
        tuple(row.geometry for row in sketch.entities),
        0.0,
        intent.recipe.DepthValue * 1000,
    )
    boundary = topology_compare(native, generated, intent.recipe.BodyId)
    measures = rectangular_source_measure(native)
    assert abs(volume - measures["volume_mm3"]) <= 1e-9
    assert abs(area - measures["area_mm2"]) <= 1e-9
    assert all(
        abs((getattr(bounds.minimum, axis) + getattr(bounds.maximum, axis)) / 2 - value) <= 1e-9
        for axis, value in zip(("x", "y", "z"), measures["center_mm"], strict=True)
    )

    assert definition.definition.second_end_condition is None
    inactive = definition.definition.second_length
    (inactive_driver,) = (
        row
        for row in document.parameters
        if row.owner_id == definition.id and row.attributes.get("freecad_path") == "Length2"
    )
    assert inactive_driver.value == inactive and inactive.unit == "mm"
    assert inactive.value != graph["ordinary_dormant_driver"]["value_mm"]
    (refine,) = (
        row
        for row in document.parameters
        if row.owner_id == definition.id and row.attributes.get("freecad_path") == "Refine"
    )
    mutations = dict(corner_faults(document, sketch, intent))
    faults = {
        fault: refuse(lambda: plan_corner(altered, case_id), reason)
        for fault, (altered, reason) in mutations.items()
    }
    return {
        "native_graph": graph,
        "production_refusals": before,
        "synthetic_owner_refusals": faults,
        "opaque_payload_count": len(document.brep_payloads),
        "other_property_parameter_names": [
            row.name for row in document.parameters if row.id not in intent.source_parameter_ids
        ],
        "additional_origins": sorted(
            row["type_id"]
            for row in document.metadata["freecad"]["objects"]
            if row["type_id"] == "App::Point"
        ),
        "inactive_source_driver": {"parameter": inactive_driver.id, "value_mm": inactive.value},
        "source_refine": refine.value.value,
        "element_map_payload_owners": [
            row.id for row in document.brep_payloads if row.attributes.get("freecad_sidecars")
        ],
        "source_body_name": intent.source_body_name,
        "source_metrics": measures,
        "body_boundary": {key: boundary[key] for key in ("faces", "edges", "vertices")},
    }


def corner_faults(document, sketch, intent):
    (anchor,) = (row for row in sketch.constraints if row.id == intent.origin_rule_id)
    native, slots = (anchor.attributes[value] for value in ("freecad", "freecad_reference_slots"))
    false = replace(
        anchor,
        attributes={
            **anchor.attributes,
            "freecad": {**native, "Second": "-2"},
            "freecad_reference_slots": (
                slots[0],
                {**slots[1], "freecad_geometry_index": -2},
                slots[2],
            ),
        },
    )
    joins = set(intent.local_rule_ids[:1])
    wrong_operand = replace(anchor, references=(replace(anchor.references[0], point="end"),))
    for label, rules, reason in (
        (
            "wrong_local_origin_slot",
            tuple(false if row is anchor else row for row in sketch.constraints),
            "unqualified external source rule owner",
        ),
        (
            "changed_neutral_operand",
            tuple(wrong_operand if row is anchor else row for row in sketch.constraints),
            "portable constraint operands differ",
        ),
        (
            "coincident_coordinates_without_authored_join",
            tuple(row for row in sketch.constraints if row.id not in joins),
            "full source rule inventory",
        ),
    ):
        yield label, (replace(document, sketches=(replace(sketch, constraints=rules),)), reason)
    (feature,) = document.feature_timeline
    draft = replace(feature.definition.draft_angle, value=1.0)
    yield "unrepresented_active_draft", (
        replace(
            document,
            feature_timeline=(
                replace(feature, definition=replace(feature.definition, draft_angle=draft)),
            ),
        ),
        "one active end without offset or draft",
    )
    (depth,) = (row for row in document.parameters if row.id == intent.source_parameter_ids[2])
    wrong_depth = replace(
        depth, expression=replace(depth.expression, parameter_ids=intent.source_parameter_ids[1:2])
    )
    altered = replace(
        document,
        parameters=tuple(wrong_depth if row is depth else row for row in document.parameters),
    )
    yield "wrong_formula_operand", (altered, "one owned local width-to-depth equation")


def measure(census):
    method = Path(__file__)
    projection = method.with_name("PlanFcstdCorner.py")
    method_pin = sha(method.read_bytes())
    projection_pin = sha(projection.read_bytes())
    src = check_output(("git", "-C", str(ROOT), "rev-parse", "HEAD:src"), text=True).strip()
    expected = check_output(("git", "-C", str(ROOT), "rev-parse", BASE + ":src"), text=True).strip()
    assert src == expected
    if check_output(("git", "-C", str(ROOT), "diff", "--name-only", "HEAD", "--", "src")):
        raise ValueError("the source tree differs from the pinned production revision")
    raw = census.read_bytes()
    assert sha(raw) == CENSUS
    pins = {**PINS, "C059-P01": SHEET}
    rows = {row["case_id"]: row for row in loads(raw)["files"] if row["case_id"] in pins}
    assert {case: row["sha256"] for case, row in rows.items()} == pins
    observed = {}
    for case, row in sorted(rows.items()):
        request = {"case_id": case, "source": row["source_path"], "sha256": row["sha256"]}
        repeats = 1 if case == "C059-P01" else 2
        results = []
        for _ in range(repeats):
            child = run(
                (sys.executable, "-I", "-B", __file__, "--worker"),
                input=wire(request),
                capture_output=True,
                timeout=60,
            )
            if child.returncode or child.stderr:
                sys.stderr.buffer.write(child.stderr)
                raise ValueError(f"{case} guarded source observation failed")
            results.append(loads(child.stdout))
        assert all(result == results[0] for result in results)
        observed[case] = results[0]
    assert sha(method.read_bytes()) == method_pin
    assert sha(projection.read_bytes()) == projection_pin
    return {
        "schema": "kit.sw2026.fcstd-corner-owned-graph.v1",
        "sdk_base": BASE,
        "production_tree": src,
        "inventory_sha256": CENSUS,
        "method_sha256": method_pin,
        "projection_sha256": projection_pin,
        "cases": observed,
        "fresh_processes": 7,
        "native_files_generated": 0,
        "native_launches": 0,
        "native_acceptance": False,
        "independently_authored_positive_designs": 1,
        "production_corpus_credit": 0,
        "historical_benchmark_membership_verified": False,
    }


def main():
    if sys.flags.optimize:
        raise ValueError("run with proof assertions enabled")
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--verified-inventory", type=Path)
    parser.add_argument("--output", type=Path)
    values = parser.parse_args()
    if values.worker:
        sys.stdout.buffer.write(wire(run_case(loads(sys.stdin.buffer.read()))))
        return
    if values.verified_inventory is None or values.output is None:
        parser.error("--verified-inventory and --output are required")
    result = wire(measure(values.verified_inventory))
    with values.output.open("xb") as stream:
        stream.write(result)
    print(sha(result))


if __name__ == "__main__":
    main()
