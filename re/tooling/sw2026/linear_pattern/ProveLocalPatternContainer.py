from argparse import ArgumentParser
from dataclasses import asdict, replace
from math import cos, dist, isclose, radians, sin
from pathlib import Path
from subprocess import run
import json
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent), str(HERE.parents[1]), str(HERE.parents[1] / "serial")]

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Construction.Dimensions.ReadModelLinear import ReadModelLinear
from convert.adapters.solidworks.Archive.Resolved.ResolvedGraph import ResolvedGraph
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Patterns.ReadPatDrivers import ReadPatDrivers

from CheckPatternAngleOwners import annotation_catalog, node_fields, point, require, selected_target
from MakeLocalPatternDrivers import DRIVER_SLOTS, PatternDriverStyle
from MakePatternAngularPlane import AngularPlaneIntent
from MakePatternAnnotationCatalog import WORLD
from PatternAngleWire import read_resolved, write_resolved
from PatternDatumHeightContrast import prediction
from PatternEnvelopeSpec import measure, specification
from ProvePatternAngleArc import span_report
from ProvePatternAngleOwners import exact_config
from ProvePatternPlaneDirectionRule import Image, MODULES, digest, document_rows, encode, module
from ProvePatternSeed import MODEL_CASES


SPANS = {
    "pattern_owner_ctor": (0x4BFBB9D0, 0x4BFBBBFB, "f4dc9d130a734302806066de1d75c99d9c50b069584b35b3bec3904421ee1e30"),
    "pattern_base_owner_ctor": (0x4C0423D0, 0x4C042801, "8456291a5a731ec7985c63414aa60033233a4d50b4210cd858b9c7501850eb4d"),
    "line_and_six_driver_factory": (0x4BFE62B0, 0x4BFE6578, "9259a5c8c6f884307b809f23d50927f3e6875efcdbd714a750fbd13f13f82c94"),
    "pattern_original_dim_ctor": (0x4C041560, 0x4C041780, "8fd8e38b37498d097f98bf76b121c0178acc624305abd08975d141321fd46421"),
    "pattern_shape_ctor": (0x4C042DF0, 0x4C042E9D, "e4c697307cb9259aed120f17ab9493c3f8e5fe0d77d0d47b22e13f0025a26d2f"),
    "single_stock_scope_transition": (0x4C044EC0, 0x4C046D76, "ae6f00b232a5bdbca095332cd4a3a9480f48d5ba3cdccc41de6be31c9fca423c"),
    "pattern_visual_application": (0x4C0481D0, 0x4C048B05, "55ab9358dea60022f6dad4345ff2904bc03a28144a0fd2dc974f766a96476670"),
    "ordinary_number_display_ctor": (0x4C86F550, 0x4C86FD02, "fcb0bf4d329370dc77bfcf4bf61deb35930516c9185f03be84cea0ee59e64f62"),
    "ordinary_distance_display_ctor": (0x4C8A4840, 0x4C8A4903, "0b62ceeb9427a41911a579a302411f03b16489473022c54e4c516856f306314c"),
}
COMPARISON_SCOPE = ("Contents/Config-0-ResolvedFeatures", "swXmlContents/KeyWords")
STYLE_FIELDS = ("fb68", "fb6c", "ff00", "f8ec", "fe40")


def static_owners(directory):
    image = Image(directory / "sldmodu.dll")
    entry = module(image, MODULES[image.path.name])
    return {"module": entry, "exact_boundaries": span_report(image, SPANS)}


def request(seed, angle, pitch, count, reverse, view_order):
    back = ((-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, -1.0))
    _, max_seed = seed.seed.bounds_m
    label = (max_seed[0] / 2, max_seed[1] / 2)
    seed = replace(seed, path=fr"C:\KitGeneratedLocalPattern\{seed.name}.SLDPRT")
    return {"seed": asdict(seed), "axis": seed.name + " hinge",
            "plane": asdict(AngularPlaneIntent(seed.name + " direction", radians(angle), False, "*Back", True, 0, (0.0, 0.0, 0.0))),
            "annotation": {"views": [{"name": name, "basis": back if name == "*Back" else WORLD} for name in view_order],
                           "active": None, "shown": [None]},
            "pattern": {"name": seed.name + " feature pattern", "count": count, "pitch_m": pitch, "reverse": reverse,
                        "styles": [asdict(PatternDriverStyle(name, "*Back" if name == "D1" else None,
                                                           ((0.0, 0.0, 0.0) if name == "D3" else (label[0], label[1] + index * .001, 0.0)), True, 0))
                                   for index, (_, name, _) in enumerate(DRIVER_SLOTS)]}}


def authored_layouts():
    one, two = MODEL_CASES
    one = replace(one, name="ColdRaisedPatternA",
                  seed=replace(one.seed, bounds_m=((.047, .042, 0.0), (.057, .054, .01375))))
    two = replace(two, name="ColdRaisedPatternB",
                  plate=replace(two.plate, bounds_m=((0.0, 0.0, 0.0), (.128, .122, .00475))),
                  seed=replace(two.seed, bounds_m=((.058, .031, 0.0), (.073, .045, .01625))))
    return ((request(one, 33.0, .018, 3, False, ("*Back", "*Front")), .024),
            (request(two, 57.0, .019, 4, True, ("*Front", "*Back")), .022))


def independent_measure(data):
    stock = data["seed"]["plate"]["bounds_m"]
    seed = data["seed"]["seed"]["bounds_m"]
    angle = data["plane"]["angle_rad"]
    intent = data["pattern"]
    sign = -1.0 if intent["reverse"] else 1.0
    axis = cos(angle) * sign, -sin(angle) * sign, 0.0
    pieces = tuple(tuple(tuple(coord + axis[index] * instance * intent["pitch_m"]
                              for index, coord in enumerate(endpoint)) for endpoint in seed) for instance in range(intent["count"]))
    result = measure((stock, *pieces))
    return {"signed_direction": axis, "body_count": 1, "face_count": 6 + 5 * intent["count"], "boxes_m": pieces,
            **{key: result[key] for key in ("volume_m3", "area_m2", "centroid_m", "bounds_m")}}


def candidate(data, *, binary=False, repeat=False):
    neutral = encode(data)
    command = (sys.executable, "-I", "-B", str(HERE.with_name("LocalPatternContainerProcess.py")))
    first = run(command, input=neutral, cwd=ROOT, capture_output=True, timeout=30)
    require(first.returncode == 0 and not first.stderr, "guarded local pattern did not emit\n" + first.stderr.decode())
    if repeat:
        second = run(command, input=neutral, cwd=ROOT, capture_output=True, timeout=30)
        require(second.returncode == 0 and not second.stderr and second.stdout == first.stdout,
                "same modeled pattern is not deterministic in fresh process")
    report = json.loads(first.stdout)
    reference = independent_measure(data)
    observed = report["observed"]
    geometry = report["analytic_geometry"]
    require(dist(reference["signed_direction"], observed["signed_direction"]) < 2e-15
            and dist(reference["centroid_m"], geometry["centroid_m"]) < 3e-16
            and all(isclose(reference[key], geometry[key], rel_tol=1e-14) for key in ("volume_m3", "area_m2"))
            and reference["bounds_m"] == tuple(geometry["bounds_m"]) and geometry["body_count"] == reference["body_count"]
            and geometry["face_count"] == reference["face_count"]
            and all(dist(a, b) < 2e-15 for expected, rows in zip(reference["boxes_m"], geometry["instance_boxes_m"], strict=True)
                    for a, b in zip(expected, rows, strict=True))
            and observed["root_count"] == 24 and report["typed_replay_count"] == 9 and report["guarded_runtime_reads"] == 0
            and observed["driver_order"] == ["D1", "D3", "D2", "D4", "D5", "D6"]
            and observed["atom_ids"] == [101, 102, 103] and observed["next_display_id"] == 12
            and len(report["bad_input"]) == 5 and len(report["bad_readback"]) == 9,
            "generated stream or geometry disagrees with independent physical cells or explicit ownership")
    receipt = {"input_sha256": digest(neutral), "modeled_input": data, "independent_cell_measure": reference, **report}
    output = None
    if binary:
        result = run((*command, "--binary"), input=neutral, cwd=ROOT, capture_output=True, timeout=30)
        require(result.returncode == 0 and not result.stderr and len(result.stdout) == report["native_container"]["bytes"]
                and digest(result.stdout) == report["native_container"]["sha256"], "binary stream changed across process boundary")
        output = result.stdout
    return receipt, output


def disclosed_owners(share):
    source = specification()
    heights = prediction()
    rectangle_inputs = {
        "DirectionEnvelope.SLDPRT": (source["seed_box_m"], source["arms"][0]),
        "DirectionEnvelopeSpacing.SLDPRT": (source["seed_box_m"], source["arms"][1]),
        "DatumHeightShort.SLDPRT": (heights["arms"][0]["seed_box_m"], {"spacing_m": heights["arms"][0]["spacing_m"], "count": 2}),
        "DatumHeightTall.SLDPRT": (heights["arms"][1]["seed_box_m"], {"spacing_m": heights["arms"][1]["spacing_m"], "count": 2}),
    }
    audit = {}
    for path, pin, _ in document_rows(share):
        if path.name not in rectangle_inputs:
            continue
        archive, headers, config, config_raw = exact_config(path, pin)
        context = MakeLinkContext(config, ReadCmgrMut(archive.Require("Contents/CMgr"), 19000))
        raw = archive.Require("Contents/Config-0-ResolvedFeatures")
        roots, extra, mapping = read_resolved(raw, config.MapValue, context, source_replay=True)
        replay, repeated = write_resolved(roots, extra, config.MapValue, context, source_replay=True)
        require(replay == raw and repeated == mapping, "disclosed warm pattern lost its exact archive")
        model = config.RootValue
        link = NativeLink(config, ResolvedGraph(roots, extra, mapping, config.MapValue.CounterValue, 19000, context, {}),
                          "Config-0", "Config-0-ResolvedFeatures")
        pattern = roots[-1]
        values = node_fields(pattern, "moLPattern_c")
        plane, _ = selected_target(node_fields(values["f1288"], "moLineRef_w"), "moCompRefPlane_c", "moRefPlane_c", model, roots, headers)
        driver_rows = ReadPatDrivers(link, pattern)
        count, pitch, *_ = driver_rows
        actual_ids = [row.DimensionValue.FieldsValue["f50"] for row in driver_rows]
        require(len(roots) == 24 and actual_ids == list(range(plane.FieldsValue["f08"] + 1, values["f08"]))
                and (count.DisplayValue.FieldsValue["f58"], pitch.DisplayValue.FieldsValue["f58"], model.FieldsValue["fd44"]) == (11, 10, 12),
                "saved pattern display and persistent allocations did not preserve independent orders")
        seed, predicted = rectangle_inputs[path.name]
        start = tuple(seed[0])
        sign = -1 if values["f1298"] else 1
        normal = source["direction_datum"]["required_signed_normal"]
        end = tuple(coord + basis * sign * predicted["spacing_m"] for coord, basis in zip(start, normal, strict=True))
        witnesses = tuple(point(pitch.DimensionValue.FieldsValue[key]) for key in ("f80", "fa0"))
        require(dist(start, witnesses[0]) < 1e-15 and dist(end, witnesses[1]) < 1e-15
                and (count.LiveValue, pitch.LiveValue) == (predicted["count"], predicted["spacing_m"]),
                "disclosed actual D3 endpoints differ from independently authored seed and motion")
        style = ReadModelLinear(model).ProjectionValue
        require(all(row.DisplayValue.FieldsValue[key] == style[key] for row in driver_rows
                    if row.DimensionValue.ClassValue.NameValue == "ParallelPlaneDistanceDim_c" for key in STYLE_FIELDS)
                and (values["f9f0"], values["f1054"]) == (1, 1),
                "native-saved distance presentation or warm branch changed its model owner")
        names = {view["f360"]: view["f358"] for view in annotation_catalog(model)}
        require(names[count.DisplayValue.FieldsValue["f2b0"][0]["v"]] == "*Back"
                and pitch.DisplayValue.FieldsValue["f2b0"] == [{"v": 199}],
                "native active display uses a different annotation view")
        audit[path.name] = {
            "source_sha256": pin, "linked_replay": {"Config-0": digest(config_raw), "Config-0-ResolvedFeatures": digest(raw)},
            "wire_line_owner_id": plane.FieldsValue["f08"], "pattern_id": values["f08"], "driver_ids": actual_ids,
            "stored_witnesses_m": witnesses, "independent_witnesses_m": (start, end),
            "active_display_ids": [11, 10], "next_model_display_id": model.FieldsValue["fd44"],
            "active_annotation_roles": ["*Back", 199],
            "actual_model_distance_style": {key: style[key] for key in STYLE_FIELDS},
            "wire_count_pitch": [count.LiveValue, pitch.LiveValue],
            "line_f0c": values["f1288"].FieldsValue["f0c"],
            "warm_scope_and_visual_application": [values["f9f0"], values["f1054"]],
        }
    require(len(audit) == len(rectangle_inputs), "required exact oblique source disclosures are missing")
    return audit


def model_cases(output_dir):
    receipts, files = {}, {}
    for base, alternate_spacing in authored_layouts():
        key = base["seed"]["name"]
        initial, output = candidate(base, repeat=True, binary=output_dir is not None)
        spacing, _ = candidate({**base, "pattern": {**base["pattern"], "pitch_m": alternate_spacing}})
        count, _ = candidate({**base, "pattern": {**base["pattern"], "count": base["pattern"]["count"] + 1}})
        for edit in (spacing, count):
            changed = tuple(sorted(name for name, old in initial["streams"].items() if edit["streams"][name] != old))
            require(changed == COMPARISON_SCOPE and initial["map_counters"] == edit["map_counters"]
                    and initial["observed"]["driver_ids"] == edit["observed"]["driver_ids"]
                    and initial["observed"]["selected_line"] == edit["observed"]["selected_line"],
                    "changing one pattern driver mutated unrelated generated stream, allocation or datum placement")
        require(initial["analytic_geometry"]["volume_m3"] == spacing["analytic_geometry"]["volume_m3"]
                and initial["analytic_geometry"]["volume_m3"] < count["analytic_geometry"]["volume_m3"],
                "independent edit predictions failed to distinguish spacing from quantity")
        receipts[key] = {"original": initial, "pitch_only": spacing, "count_only": count}
        if output is not None:
            files[key + ".SLDPRT"] = output
    return receipts, files


def main():
    parser = ArgumentParser()
    parser.add_argument("--share", required=True, type=Path)
    parser.add_argument("--binaries", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--candidate-directory", type=Path)
    args = parser.parse_args()
    require(not args.output.exists(), "choose a fresh local pattern receipt")
    if args.candidate_directory is not None:
        require(args.candidate_directory.is_dir() and not any(args.candidate_directory.iterdir()),
                "optional binary transport requires an existing empty owned candidate directory")
    authority = static_owners(args.binaries)
    cases, files = model_cases(args.candidate_directory)
    warm = disclosed_owners(args.share)
    paths = tuple(HERE.with_name(name + ".py") for name in ("ProveLocalPatternContainer", "LocalPatternContainerProcess",
                  "EmitLocalPattern", "MakeLocalPattern", "MakeLocalPatternDrivers", "PatternBoxGeometry", "MakePatternSeed",
                  "MakePatternAngularPlane", "PatternAngleWire"))
    receipt = {"schema": "kit.sw2026.local-linear-pattern-model-only-candidate.v1", "build": "34.5.2.0604", "native_lifecycles": 0,
               "host_only": True, "heldout_cases": 0, "static_owners": authority, "warm_replay": warm, "model_cases": cases,
               "guarded_processes": 8 + (2 if args.candidate_directory else 0),
               "changed_streams_for_each_independent_edit": COMPARISON_SCOPE,
               "tools": {str(path.relative_to(ROOT)): digest(path.read_bytes()) for path in paths}}
    for name, data in files.items():
        with (args.candidate_directory / name).open("xb") as output:
            output.write(data)
    with args.output.open("xb") as sink:
        sink.write(encode(receipt))
    print(json.dumps({"receipt_sha256": digest(args.output.read_bytes()), "modeled_neutral_cases": len(cases),
                      "exact_native_source_audits": len(warm),
                      "candidate_containers": {name: row["original"]["native_container"] for name, row in cases.items()}},
                     sort_keys=True))


if __name__ == "__main__":
    main()
