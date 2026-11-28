from argparse import ArgumentParser
from dataclasses import dataclass, replace
from enum import Enum
from importlib.metadata import version
from platform import python_version
from pathlib import Path
from struct import unpack_from
from subprocess import run
import json
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

import MeasureWarmNestedLeaf as warm
from MeasureSavedEndWords import WARM_PIN, authority, bound_tool
from TraceFirstCreatorScope import trace_scope

from convert.adapters.solidworks.Archive.Construction.Part.EmitPartStreams import EmitPartStreams
from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismAtom import CheckPrismAtom


BASIS = "f7e0266527dfcb0e37e47056b6b04b47f57beed6"
MEASURES = warm.ROOT / "re/solidworks/measurements/2026"
END_SCOPE_PIN = "f96930c3a407dbb01aaa6fe6d337b545b55732f0101f63e63a4ad94caf90f4ed"
RESOLVED = "Contents/Config-0-ResolvedFeatures"
CASE_LOCATOR = "C:\\KitWarmFirstCreatorScope\\"
EXPECTED_SCOPE = {"first_existing_body_scope": "selected", "prior_body_ids": []}


class ExistingBodies(Enum):
    All = "all"
    Selected = "selected"


@dataclass(frozen=True, slots=True)
class FirstCreatorScope:
    mode: ExistingBodies
    prior_body_ids: tuple[str, ...] = ()

    @classmethod
    def from_data(cls, data):
        warm.require(type(data) is dict and set(data) == {"first_existing_body_scope", "prior_body_ids"}
                     and type(data["prior_body_ids"]) is list,
                     "first-creator scope requires only its existing-body mode and explicit prior targets")
        return cls(ExistingBodies(data["first_existing_body_scope"]), tuple(data["prior_body_ids"]))


class Guard(warm.BuildAudit):
    def InspectEvent(self, event, args):
        if event.startswith(("socket.", "ctypes.", "winreg.")) or event in ("os.startfile", "os.rename", "os.remove"):
            self.DeniedReads.append(event)
            raise PermissionError("construction attempted native invocation or file mutation")
        return super().InspectEvent(event, args)


def first_creator(document, scope):
    warm.require(type(scope) is FirstCreatorScope and type(scope.mode) is ExistingBodies,
                 "first creator requires an explicit existing-body policy")
    warm.require(scope.prior_body_ids == (), "standalone first creator cannot select an existing body")
    warm.require(len(document.feature_timeline) == len(document.bodies) == len(document.sketches) == 1
                 and not (document.selections or document.brep or document.brep_payloads),
                 "first-creator scope requires a single fresh neutral rectangle and no inherited bodies")
    feature, = document.feature_timeline
    body, = document.bodies
    warm.require(feature.operation == warm.BooleanOp.KCreate and not (feature.input_feature_ids or feature.selection_ids)
                 and type(feature.definition) is warm.ExtrudeFeature and feature.definition.end_condition == warm.ExtrudeEnd.KBlind
                 and feature.sketch_id == document.sketches[0].id and body.final_feature_id == feature.id,
                 "scope belongs to the actual first solid producer, not a join or dependency")
    return body


def check_fresh_owner(candidate):
    model = candidate.SystemValue.RootValue
    boss = candidate.BossValue.FeatureValue
    manager = model.FieldsValue["fd88"]
    warm.require(candidate.CutValue is None and candidate.ResolvedValue.RootsValue[-1] is boss
                 and boss.ClassValue.NameValue == "moExtrusion_c"
                 and model.FieldsValue["fd90"]["n"] == 0
                 and manager["n6c"] == 0 and not manager["atoms"]
                 and model.FieldsValue["fe38"] is None
                 and all(field not in boss.FieldsValue for field in ("f548", "f558")),
                 "fresh standalone boss has retained body selection, manager rows, or rollback history")
    CheckPrismAtom(boss)
    return boss


def construct(document, scope, labels, modes):
    body = first_creator(document, scope)
    config, = document.configurations
    name = document.metadata["name"]
    component = warm.ComponentDef("leaf/" + name, name, "part", configuration_name=config.name,
                                  configuration_id=config.id, body_ids=(body.id,))
    leaf = warm.ReadNestedLeaf(component, document)
    plan = leaf.PartValue
    recipe = replace(warm.MakePartRecipe(plan, warm.TARGET_INSTANT),
                     OutputValue=warm.SelfFileInput(CASE_LOCATOR + name + ".SLDPRT", warm.TARGET_INSTANT))
    layout = warm.RectDimInput(tuple(labels[0][:2]), tuple(labels[1][:2]), *modes)
    initial = warm.MakeRectDimPart(leaf.DocumentValue, recipe, layout)
    dimensions = tuple(warm.DimensionGraph(parameter, dim, row.FieldsValue["f850"][0]["o"], row)
                       for row, dim, parameter in warm.actual_displays(initial.ProfileValue.ProfileValue))
    keys = warm.MakeSketchKeys(dimensions, recipe.DocumentUnits.LengthUnit)
    spatial, _, _, spatial_delta = warm.compose_text_mut(initial, recipe, keys, labels)
    boss = check_fresh_owner(spatial)
    scope_code = int(scope.mode is ExistingBodies.Selected)
    boss.FieldsValue["f544"] = scope_code
    streams, cfg, resolved = EmitPartStreams(
        spatial.SystemValue, spatial.ResolvedValue.RootsValue, (spatial.HeaderValue, spatial.TopHeader, spatial.ManagerHeader),
        spatial.DefinitionValue, recipe, plan, keys,
    )
    return replace(spatial, ConfigValue=cfg, ResolvedValue=resolved, StreamsValue=streams,
                   BytesValue=BuildSldprt(streams, FormatVersion=4)), plan, spatial_delta


def read_owners(candidate):
    archive = warm.SldprtArchive.from_bytes(candidate.BytesValue)
    warm.require(archive.streams == candidate.StreamsValue and warm.PARTITION not in archive.streams,
                 "independent container decoding differs or contains retained geometry")
    link = warm.ReadNativeLink(archive, 0)
    features = warm.IndexFeatures(link)
    warm.CheckSingleBoss(features, "moExtrusion_c")
    boss, = (row for row in features.values() if row.ClassValue.NameValue == "moExtrusion_c")
    owner = warm.ReadExtrude(link, boss, features)
    manager = link.ConfigValue.RootValue.FieldsValue["fd88"]
    warm.require(owner.ParentsValue == (owner.ProfileValue,)
                 and features[warm.NativeNodeId(owner.ProfileValue)] is owner.ProfileValue
                 and owner.ModeValue == warm.ExtrudeEnd.KBlind and not owner.IsReversed
                 and manager["n6c"] == 0 and not manager["atoms"]
                 and all(not boss.FieldsValue[key] for key in ("has_f548", "has_f528", "has_f530", "has_f3d0"))
                 and not set(boss.FieldsValue) & {"f548", "f558"},
                 "fresh typed owner differs from the actual profile or has attachment state")
    depth = owner.RequireDepth().DepthValue
    owner_view = {
        "feature": warm.NativeNodeSpan(link, boss), "profile": warm.NativeNodeSpan(link, owner.ProfileValue),
        "depth": depth.TypedOwner, "depth_m": depth.native_value,
        "system_feature_ids": sorted(features),
        "atom_count": manager["n6c"], "scope": boss.FieldsValue["f544"], "selected_wrappers": 0,
    }
    return boss, owner_view


def public_history(value, *, include_brep):
    model = warm.open_document(value, source_format=warm.FORMAT, include_brep=include_brep)
    selected_id, = (body.final_feature_id for body in model.bodies)
    owner, = (row for row in model.feature_timeline if row.id == selected_id)
    return model, {
        "feature_name": owner.name, "operation": str(owner.operation), "definition": warm.ToData(owner.definition),
        "constraints": len(model.sketches[0].constraints), "editable_parameters": [
            [row.name, row.role, row.value.value] for row in model.parameters
        ],
    }


def compare(job):
    document = warm.FromData(job["document"])
    document.assert_valid()
    warm.InferCaps(document)
    document.to_json()
    captured = FirstCreatorScope.from_data(job["scope"])
    warm.require(captured.mode is ExistingBodies.Selected, "source proof requires its actual selected mode")
    labels, modes = job["label_points"], job["dimension_modes"]
    warm.primed()
    guard = Guard(HERE.parent)
    sys.addaudithook(guard.InspectEvent)
    guard.BeginBuild()
    control, plan, label_delta = construct(document, FirstCreatorScope(ExistingBodies.All), labels, modes)
    variant, _, selected_label_delta = construct(document, captured, labels, modes)
    warm.require(label_delta == selected_label_delta == [RESOLVED], "spatial label variant touched another archive")
    changed = [stream for stream, raw in control.StreamsValue.items() if variant.StreamsValue[stream] != raw]
    warm.require(control.StreamsValue.keys() == variant.StreamsValue.keys() and changed == [RESOLVED],
                 "existing-body scope changed a stream other than its feature owner")
    before, after = control.StreamsValue[RESOLVED], variant.StreamsValue[RESOLVED]
    difference, = (i for i, (x, y) in enumerate(zip(before, after, strict=True)) if x != y)
    control_boss, control_owner = read_owners(control)
    selected_boss, selected_owner = read_owners(variant)
    warm.require(control_owner["scope"] == 0 and selected_owner.pop("scope") == 1
                 and replace_owner_scope(control_owner) == selected_owner
                 and control_owner["feature"]["offset"] <= difference < control_owner["feature"]["end"] - 3
                 and unpack_from("<i", before, difference) == (0,) and unpack_from("<i", after, difference) == (1,),
                 "changed byte does not encode exactly the same first boss's persisted scope")
    CheckPrismAtom(control_boss)
    typed_refusal = warm.refusal(lambda: CheckPrismAtom(selected_boss), "ValueError",
                                 "cache free prism has atom attachment or modifier flags")
    qualified, strict_history = public_history(control.BytesValue, include_brep=True)
    _, control_no_brep = public_history(control.BytesValue, include_brep=False)
    selected_meta, selected_no_brep = public_history(variant.BytesValue, include_brep=False)
    warm.require(control_no_brep == selected_no_brep and selected_meta.brep is None,
                 "existing-body scope modifies metadata-only editable history")
    public_refusal = warm.refusal(lambda: public_history(variant.BytesValue, include_brep=True),
                                  "SldprtFormat", "SLDPRT contains no readable Parasolid payload")
    displays = warm.observe(variant.BytesValue)
    warm.require(displays == warm.observe(control.BytesValue)
                 and [displays[key]["text_m"] for key in ("width", "height")] == labels
                 and all(row["centerline_route"] == modes[2] for row in displays.values()),
                 "scope changed the actual independent sketch display fields")
    vertices = tuple((1000 * x, 1000 * y) for x, y in plan.VerticesValue)
    geometry = warm.measure_boundary(qualified.brep, qualified.bodies[0].id, vertices, document.parameters[-1].value.value)
    warm.require(not guard.DeniedReads, "fresh scope construction accessed a runtime source")
    return {
        "control_sha256": warm.digest(control.BytesValue), "selected_sha256": warm.digest(variant.BytesValue),
        "input_locator": CASE_LOCATOR + document.metadata["name"] + ".SLDPRT", "epoch": warm.TARGET_INSTANT,
        "neutral_request_sha256": warm.wire_sha(job), "control_stream_sha256": {
            name: warm.digest(raw) for name, raw in control.StreamsValue.items()
        },
        "selected_resolved_sha256": warm.digest(after), "scope_only_stream": changed[0],
        "scope_i32_offset": difference, "scope_word": [0, 1],
        "shared_owner_graph": selected_owner, "exact_display": displays,
        "ordinary_strict_history": strict_history, "ordinary_strict_geometry": geometry,
        "selected_metadata_history": selected_no_brep,
        "selected_default_strict_refusal": public_refusal, "selected_typed_geometry_refusal": typed_refusal,
        "construction_runtime_reads": 0, "binary_files_published": 0,
    }


def replace_owner_scope(owner):
    return {key: value for key, value in owner.items() if key != "scope"}


def negatives(job):
    doc = warm.FromData(job["document"])
    scope = FirstCreatorScope.from_data(job["scope"])
    feature, = doc.feature_timeline
    body, = doc.bodies
    guard = Guard(HERE.parent)
    sys.addaudithook(guard.InspectEvent)
    guard.BeginBuild()
    failures = {
        "operation_join": warm.refusal(
            lambda: first_creator(replace(doc, feature_timeline=(replace(feature, operation=warm.BooleanOp.KJoin),)), scope),
            "ValueError", "scope belongs to the actual first solid producer"
        ),
        "selected_output_itself": warm.refusal(
            lambda: first_creator(doc, replace(scope, prior_body_ids=(body.id,))),
            "ValueError", "standalone first creator cannot select an existing body"
        ),
        "extra_body": warm.refusal(
            lambda: first_creator(replace(doc, bodies=(body, replace(body, id=body.id + ":other"))), scope),
            "ValueError", "first-creator scope requires a single fresh neutral rectangle"
        ),
        "runtime_auto_option": warm.refusal(
            lambda: FirstCreatorScope.from_data({**job["scope"], "auto_select": True}),
            "ValueError", "first-creator scope requires only its existing-body mode"
        ),
    }
    warm.require(not guard.DeniedReads, "scope refusals attempted external access")
    return failures


def invoke(phase, data):
    result = run((sys.executable, "-I", "-B", str(HERE), "--worker", phase), input=json.dumps(data),
                 capture_output=True, text=True, timeout=90)
    diagnostic = result.stderr[-3600:] or "first-creator scope worker did not complete"
    warm.require(result.returncode == 0 and not result.stderr, f"{phase}: {diagnostic}")
    return json.loads(result.stdout)


def supervise(workspace, modules):
    warm.require(warm.git("rev-parse", "HEAD:src").decode().strip() == warm.SOURCE_TREE
                 and not warm.git("status", "--porcelain", "--", "src"), "first-creator proof requires the pinned SDK")
    warm_receipt = authority(MEASURES / "SdkWarmNestedLeaf01.json", WARM_PIN)
    receipt = authority(MEASURES / "SdkWarmSavedEndWords01.json", END_SCOPE_PIN)
    tools = {name: bound_tool(f"re/tooling/sw2026/nested_publication/{name}", pin)
             for name, pin in warm_receipt["tool_sha256"].items()}
    static_name = "TraceSavedEndWords.py"
    tracked_path = f"re/tooling/sw2026/nested_publication/{static_name}"
    pin = receipt["tool_sha256"][static_name]
    warm.require(warm.digest(warm.git("show", f"{BASIS}:{tracked_path}")) == pin, "native evidence helper differs")
    tools[static_name] = warm.digest(warm.pinned(warm.ROOT / tracked_path, pin))
    references = {name: authority(MEASURES / name, value) for name, value in warm.PINS.items()}
    sources = tuple(warm.models(workspace, references))
    native = trace_scope(modules)
    cases, requests = {}, {}
    for source in sources:
        observed = invoke("source", source)
        name = source["name"]
        data = observed["request"]
        scope = observed["record"]["source_creator_flags"]
        warm.require(observed["file_sha256"] == receipt["cases"][name]["sha256"]
                     and scope["f544"] == 1 and scope["has_f548"] == scope["has_f530"] == 0,
                     "warm source does not bind selected scope with no prior body owner")
        request = {**data, "scope": EXPECTED_SCOPE}
        requests[name] = request
        result = invoke("compose", request)
        warm.require(not warm.differences(observed["record"]["dimension_display"], result["exact_display"]),
                     "scope candidate failed the exact source label projection")
        cases[name] = {"original_sha256": observed["file_sha256"],
                       "stored_existing_body_policy": EXPECTED_SCOPE, "cold_composition": result}
    negative = invoke("negatives", requests["SinglePlate"])
    return {
        "schema": "kit.sw2026.standalone-first-creator-scope-proof.v1", "source_tree": warm.SOURCE_TREE,
        "base_revision": BASIS, "native_static": native, "cases": cases, "negative": negative,
        "tool_runtime": {"python": python_version(), "pefile": version("pefile"), "capstone": version("capstone")},
        "prior_receipt_sha256": {"warm": WARM_PIN, "saved_end": END_SCOPE_PIN},
        "bound_helper_sha256": tools, "tool_sha256": {
            path.name: warm.digest(path.read_bytes()) for path in (HERE, HERE.with_name("TraceFirstCreatorScope.py"))
        },
        "guarded_source_workers": len(sources), "guarded_no_read_composers": len(cases),
        "native_processes_started": 0, "protected_sources_opened": 0, "binary_files_published": 0,
        "new_oracle_acceptance": False, "original_source_transfer_complete": False,
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("--disclosed", type=Path)
    parser.add_argument("--modules", type=Path)
    parser.add_argument("--worker", choices=("source", "compose", "negatives"))
    args = parser.parse_args()
    if args.worker:
        worker = {"source": warm.inspect, "compose": compare, "negatives": negatives}[args.worker]
        value = worker(json.load(sys.stdin))
    else:
        warm.require(args.disclosed is not None and args.disclosed.is_absolute()
                     and args.modules is not None and args.modules.is_absolute(),
                     "pass absolute disclosed and licensed binary roots")
        value = supervise(args.disclosed, args.modules)
    print(json.dumps(value, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
