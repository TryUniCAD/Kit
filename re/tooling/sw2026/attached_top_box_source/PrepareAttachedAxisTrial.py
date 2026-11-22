from argparse import ArgumentParser
from base64 import b64decode, b64encode
from codecs import lookup
from math import isclose
from pathlib import Path, PureWindowsPath
import json
import re
import subprocess
import sys

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from VerifyAttachedBoxAxes import intake, visibility_source
from VerifyOriginalFcstdAttachedBox import CASE, FORMAT, LOCATOR, NATIVE_SHA, ROOT, SOURCE_SHA, digest, guarded, locked, prewarm, refusal, require
from MakeAttachedAxes import coords
from MakeAttachedAxisPart import make_part
from convert import open_document
from convert.adapters.registry.RegistryErrors import NotFoundError
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PartTextInput import PartTextInput
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName, RequireNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Preparation.FreecadBox.PlanAttachedBox import PlanAttachedBox
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.ReadColdOutput import ReadColdOutput
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.document.Models.DocumentModel import CadDocument


GUEST_ROOT = PureWindowsPath(r"C:\KitAttachedBoxAxes01")
SOURCE_REVISION = "51e7b54148a8fd8ad21f88506bf68222c6f9479a"
MANIFEST_SCHEMA = "kit.sw2026.attached-box-xyz-candidate.v1"
SOURCE_CHECK_SHA = "87975399948bb31e746afc6cb6c7578b8c120201f4bb84509807ccdf0390f195"
PARENT_NAMES = (('Top Plane', 'Front Plane'), ('Front Plane', 'Right Plane'), ('Right Plane', 'Top Plane'))
CONTROL_SHA = "c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57"


def artifact(candidate):
    return {"bytes": len(candidate.BytesValue), "sha256": digest(candidate.BytesValue),
            "streams": {name: {"bytes": len(value), "sha256": digest(value)}
                        for name, value in candidate.StreamsValue.items()}}


def stock_expected(values):
    length, width, height = values
    low, high = [0., -height, 0.], [length, 0., width]
    intervals = [[a - (b-a)*0.05, b + (b-a)*0.05] for a, b in zip(low, high, strict=True)]
    return {"dimensions_m": list(values), "body_box_m": [low, high], "axis_intervals_m": intervals,
            "body_count": 1, "topology": [8, 12, 6], "volume_m3": length*width*height,
            "area_m2": 2*(length*width + length*height + width*height), "com_m": [length/2, -height/2, width/2]}


def node_fingerprint(node):
    return (node.FieldsValue["f08"], node.ClassValue.NameValue, ReadNodeName(node))


def read_axis_wire(row, root, roots, headers, created, expected_parents):
    fields = row.FieldsValue
    values = RequireNode(fields["f700"], "moPlaneInterAxisData_c").FieldsValue
    ident = fields["f08"]
    require(fields["hidden"] == 0 and all(DatumTime(header, ident) == created for header in headers),
            "axis lost its fresh log or visible feature bit")
    parents, matrices, wrappers, components = [], [], [], []
    for key in ("f80", "f88"):
        wrapper = RequireNode(values[key], "moPlaneRef_w")
        ref = RequireNode(wrapper.FieldsValue["f58"], "moCompRefPlane_c")
        comp = RequireNode(ref.FieldsValue["f58"], "moUnitComponent_c")
        owner = RequireNode(roots[ref.FieldsValue["ff0"]["f00"]], "moRefPlane_c")
        label = ReadNodeName(owner)
        basis = wrapper.FieldsValue["f100"]
        require(comp.FieldsValue["owner"] is root and comp.FieldsValue["has_ext"] == 0
                and wrapper.FieldsValue["f68"] == 1
                and all(DatumTime(header, owner.FieldsValue["f08"]) == ref.FieldsValue["ff0"]["f08"] for header in headers)
                and (basis["has_matrix"] == int(label != "Front Plane")) and (("f08" in basis) == bool(basis["has_matrix"])),
                "axis plane reference lost the actual local support or its basis")
        parents.append(label)
        matrices.append(basis["has_matrix"])
        wrappers.append(wrapper)
        components.append(comp)
    require(tuple(parents) == expected_parents, "axis changed its ordered principal plane selection")
    return {"id": ident, "name": ReadNodeName(row), "parents": parents, "matrix_flags": matrices,
            "start_m": coords(values["f18"]), "end_m": coords(values["f30"]), "direction": coords(values["f50"]),
            "anchor_m": coords(values["f68"]), "signed_lengths_m": [values["f08"], values["f10"]]}, wrappers, components


def typed_replay(candidate, plain, axes, creation, expected):
    require(all(row.FieldsValue["owner"] is candidate.SystemValue.RootValue
                for row in candidate.ResolvedValue.RootsValue[-3:]),
            "constructed axis lost its actual model owner")
    archive = SldprtArchive.from_bytes(candidate.BytesValue)
    link = ReadNativeLink(archive, 0)
    roots = IndexFeatures(link)
    base = IndexFeatures(ReadNativeLink(SldprtArchive.from_bytes(plain.BytesValue), 0))
    ordered = tuple(roots.values())
    expected_count = len(base) + len(axes)
    require(len(ordered) == expected_count and list(map(node_fingerprint, ordered[:-3])) == list(map(node_fingerprint, base.values())),
            "existing feature identities or order changed when adding axis roots")
    headers = (link.ConfigValue.HeaderValue, ReadHeaderGraph(archive.require("Header2"), 19000))
    entries, all_wrappers, all_components = [], [], []
    for index, (row, axis, parents) in enumerate(zip(ordered[-3:], axes, PARENT_NAMES, strict=True)):
        require(row.ClassValue.NameValue == "moRefAxis_c", "a named axis is not a real native feature root")
        item, wrappers, components = read_axis_wire(row, link.ConfigValue.RootValue, roots, headers, creation, parents)
        require(item["name"] == axis["name"] and item["anchor_m"] == (0.0, 0.0, 0.0)
                and tuple(item["direction"]) == tuple(1.0 if value == index else 0.0 for value in range(3))
                and all(point[axis_index] == 0.0 for point in (item["start_m"], item["end_m"])
                        for axis_index in range(3) if axis_index != index)
                and all(isclose(point[index], bound, rel_tol=0., abs_tol=1e-16)
                        for point, bound in zip((item["start_m"], item["end_m"]), expected["axis_intervals_m"][index], strict=True))
                and item["signed_lengths_m"] == [-item["start_m"][index], item["end_m"][index]],
                "typed axis differs from the independent signed-box prediction")
        entries.append(item)
        all_wrappers.extend(wrappers)
        all_components.extend(components)
    require(len(set(all_wrappers)) == len(set(all_components)) == 6,
            "ordered axis wrappers acquired a foreign shared vertex")
    config = link.ConfigValue
    resolved = link.ResolvedValue
    counter = headers[0].FieldsValue["f08"]
    require(counter == headers[1].FieldsValue["f08"] == candidate.CurrentConfig.FieldsValue["f85c"] + 1
            and max(roots) < counter, "axis allocator did not publish a consistent header frontier")
    regenerated, model = WriteConfigMut(config.RootValue, 19000, config.HeaderValue)
    expanded, graph = WriteResolMut(resolved.RootsValue, resolved.ExtraFields, 19000, model.MapValue, resolved.ContextValue)
    require(regenerated == archive.require(link.ConfigName) and expanded == archive.require(link.StreamName)
            and graph.MapValue.CounterValue == resolved.MapValue.CounterValue,
            "the generated Config and Resolved objects do not reciprocally replay")
    body = ReadColdOutput(link)
    require(body is not None and body.NameValue == "Body" and body.BossValue is ordered[-4],
            "axis publication displaced the actual named stock atom")
    return {"axes": entries, "roots": len(roots), "header_frontier": counter, "stock_body_name": body.NameValue,
            "configuration_map": config.MapValue.CounterValue, "resolved_map": resolved.MapValue.CounterValue,
            "reciprocal_streams": 2}


def guarded_worker(request):
    require(set(request) == {"document", "creation", "properties", "axes", "origin_visible", "locator"},
            "guarded axis worker accepts only the clean model instruction")
    pure = PureWindowsPath(request["locator"])
    require(pure == GUEST_ROOT / "F14c.SLDPRT", "the scoped experiment needs its actual unused model locator")
    lookup("utf-8-sig")
    prewarm()
    with guarded():
        model = CadDocument.from_json(json.dumps(request["document"], allow_nan=False))
        require(not model.brep_payloads and model.brep is None, "the guarded worker received source payloads")
        properties = PartTextInput(request["properties"]["summary"], request["properties"]["file"], {})
        creation = request["creation"]
        axes = request["axes"]
        generated = make_part(model, str(pure), creation, properties, axes, origin_visible=request["origin_visible"])
        baseline = make_part(model, str(pure), creation, properties)
        measured_locator = make_part(model, LOCATOR, creation, properties)
        plan = generated.PlanValue
        expected = stock_expected((plan.WidthValue, plan.HeightValue, plan.DepthValue))
        wire = typed_replay(generated, baseline, axes, creation, expected)
        changed = sorted(name for name in generated.StreamsValue if generated.StreamsValue[name] != baseline.StreamsValue[name])
        require(set(generated.StreamsValue) == set(baseline.StreamsValue), "XYZ graph changed the container stream set")
        bad = [dict(value) for value in axes]
        bad[0]["visible"] = False
        hidden = refusal(lambda: make_part(model, str(pure), creation, properties, bad),
                         "unsupported axis name, carrier, order or model visibility")
        wrong_order = refusal(lambda: make_part(model, str(pure), creation, properties, axes[::-1]),
                              "unsupported axis name, carrier, order or model visibility")
        public = {}
        for label, include_brep in (("default", True), ("history_only", False)):
            try:
                read = open_document(generated.BytesValue, source_format=FORMAT, strict=True, include_brep=include_brep)
            except (ValueError, NotFoundError, RuntimeError) as error:
                public[label] = {"status": "refused", "diagnostic": str(error)}
            else:
                public[label] = {"status": "read", "axis_labels": [row.name for row in read.feature_timeline
                                 if row.name in {item["name"] for item in axes}], "bodies": len(read.bodies)}
    return {"candidate": artifact(generated), "same_locator_plain": artifact(baseline), "prior_locator_plain": artifact(measured_locator),
            "candidate_b64": b64encode(generated.BytesValue).decode(), "changed_streams": changed, "expected": expected,
            "wire": wire, "strict_public_read": public, "guarded_refusals": [hidden, wrong_order], "runtime_input_file_reads": 0}


def request_for(source):
    model, raw = intake(source, SOURCE_SHA)
    plan = PlanAttachedBox(model)
    part = plan.PartSource
    require(part.UnitsValue is None, "the scoped 0.21 experiment needs the ordinary document units")
    axes = visibility_source(model, raw, plan.OriginAxes)
    return {"document": json.loads(part.ModelValue.to_json(indent=None)), "creation": part.CreationEpoch,
            "properties": {"summary": dict(part.PropertiesValue.SummaryFields), "file": dict(part.PropertiesValue.DocumentFields)},
            "axes": [{"role": row["role"], "name": row["label"], "origin": list(row["origin_mm"]),
                      "direction": list(row["direction"]), "visible": row["model_visibility"]} for row in axes["axes"]],
            "origin_visible": axes["origin_model_visibility"], "locator": str(GUEST_ROOT / "F14c.SLDPRT")}


def isolate(request):
    process = subprocess.run([sys.executable, "-I", "-B", str(HERE), "--worker"], input=json.dumps(request, allow_nan=False),
                             capture_output=True, text=True, timeout=120)
    require(process.returncode == 0 and not process.stderr, process.stderr or "clean axis construction worker failed")
    return json.loads(process.stdout)


def stage(source, output):
    request = request_for(source)
    native = json.loads(locked(ROOT / "re/solidworks/measurements/2026/AttachedTopBoxGeneratedNative01.json", NATIVE_SHA))
    _ = locked(ROOT / "re/solidworks/measurements/2026/AttachedBoxAxes01.json", SOURCE_CHECK_SHA)
    require(native["controls_healthy"] and native["oracle_file_version"] == "34.5.2.0604", "prior native receipt controls differ")
    measured = native["cases"][CASE]
    built = isolate(request)
    require(built == isolate(request), "independent guarded axis builds disagree")
    require(built["prior_locator_plain"] == {"bytes": measured["bytes"], "sha256": measured["output_sha256"],
                                            "streams": measured["streams"]},
            "stock composition no longer reproduces the previously measured axis-free file")
    payload = b64decode(built.pop("candidate_b64"), validate=True)
    require(digest(payload) == built["candidate"]["sha256"], "frozen candidate identity changed")
    dims = built["expected"]["dimensions_m"]
    require(dims == measured["native_drivers_m"], "axis trial stock differs from the exact source")
    edited = {}
    for index, (name, value) in enumerate(zip(("Length", "Width", "Height"), measured["independent_edit_values_m"], strict=True)):
        values = list(dims)
        values[index] = value
        edited[name] = stock_expected(values)
    tools = tuple(HERE.with_name(name) for name in ("MakeAttachedAxes.py", "MakeAttachedAxisPart.py", HERE.name,
                                                   "VerifyAttachedBoxAxes.py", "VerifyIntactAttachedPlan.py", "VerifyOriginalFcstdAttachedBox.py"))
    receipt = {"schema": MANIFEST_SCHEMA, "preparation_base": SOURCE_REVISION, "passed": True,
               "source_sha256": SOURCE_SHA, "source_owner_receipt_sha256": SOURCE_CHECK_SHA, "prior_native_receipt_sha256": NATIVE_SHA,
               "native_acceptance": False, "native_processes_started": 0, "benchmark_conversion_credits": 0,
               "exact_guest_locator": request["locator"], "file": "F14c.SLDPRT", "creation_epoch": request["creation"],
               "oracle": {"release": native["oracle_file_version"], "sha256": native["oracle_executable_sha256"], "control_sha256": CONTROL_SHA},
               "prospective_axes_after_edit": edited, "source_text": request["properties"],
               "axis_endpoint_refit_after_edit_unqualified": True, "native_viewport_visibility_unqualified": True,
               "tools_sha256": {path.name: digest(path.read_bytes()) for path in tools}, "fresh_guarded_workers": 2, **built}
    _ = locked(source, SOURCE_SHA)
    output.mkdir()
    with (output / receipt["file"]).open("xb") as file:
        file.write(payload)
    with (output / "Build.json").open("x", encoding="utf-8") as file:
        json.dump(receipt, file, indent=2, sort_keys=True, allow_nan=False)
        file.write("\n")
    verify(output, digest((output / "Build.json").read_bytes()))


def verify(output, freeze_sha):
    manifest = json.loads(locked(output / "Build.json", freeze_sha))
    require(manifest["schema"] == MANIFEST_SCHEMA and manifest["file"] == "F14c.SLDPRT"
            and manifest["exact_guest_locator"] == str(GUEST_ROOT / manifest["file"])
            and manifest["passed"] is True and manifest["native_acceptance"] is False
            and manifest["runtime_input_file_reads"] == 0
            and re.fullmatch(r"[0-9a-f]{64}", manifest["candidate"]["sha256"]),
            "the independent native trial needs the exact disclosed model-only candidate")
    payload = locked(output / manifest["file"], manifest["candidate"]["sha256"])
    require(len(payload) == manifest["candidate"]["bytes"], "frozen candidate size differs")
    print(json.dumps({"freeze_sha256": freeze_sha, "candidate_sha256": manifest["candidate"]["sha256"],
                      "guest_locator": manifest["exact_guest_locator"], "roots": manifest["wire"]["roots"]}, sort_keys=True))


def main():
    if sys.argv[1:] == ["--worker"]:
        print(json.dumps(guarded_worker(json.load(sys.stdin)), sort_keys=True, allow_nan=False))
        return
    parser = ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("stage")
    create.add_argument("source", type=Path)
    create.add_argument("output", type=Path)
    check = commands.add_parser("verify")
    check.add_argument("output", type=Path)
    check.add_argument("sha256")
    args = parser.parse_args()
    if args.command == "stage":
        stage(args.source, args.output)
    else:
        verify(args.output, args.sha256)


if __name__ == "__main__":
    main()
