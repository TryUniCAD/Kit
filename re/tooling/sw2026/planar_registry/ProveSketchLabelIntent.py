from argparse import ArgumentParser
from codecs import lookup
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from importlib import import_module
import json
from math import hypot, isclose
import os
from pathlib import Path, PureWindowsPath
from subprocess import check_output, run
import sys


sys.path.insert(0, str(Path(__file__).resolve().parent))
from PlanarRegistryBuild import ROOT, artifact, bind, fingerprint, require, write


BASE = "03e2e5ed376229565c6d381b132dd1c946d89218"
HERE = Path(__file__).resolve()
BUILDER = HERE.with_name("SketchLabelIntent.py")
RESOLVED = "Contents/Config-0-ResolvedFeatures"
CONFIG = "Contents/Config-0"
EVENT = 1794001931


def audit_link(bundle):
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadLineDims import ReadLineDims
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from RectanglePresentation import point

    child = SldprtArchive.from_bytes(bundle.ChildValue.BytesValue)
    parent = SldprtArchive.from_bytes(bundle.BytesValue)
    require(child.streams == bundle.ChildValue.StreamsValue and parent.streams == bundle.StreamsValue,
            "the complete generated streams must equal the linked modeled streams")
    link = ReadNativeLink(child, 0)
    profile, = (node for node in link.ResolvedValue.RootsValue if isinstance(node, ArchiveNode)
                and node.ClassValue.NameValue == "moProfileFeature_c" and ReadNodeName(node) == "Sketch1")
    sketch = ArchiveNode.RequireNode(profile.FieldsValue["pd_f80"])
    dims = sketch.FieldsValue["dims"]
    actual = {}
    for driver in ReadLineDims(sketch, link).DriverValues:
        value, parameter = driver.NodeValue, driver.ParamValue
        handle, display, slot = driver.HandleValue, driver.DisplayValue, driver.IndexValue
        fields = display.FieldsValue
        require(dims["val_g2"][slot]["d"] is value and value.FieldsValue["f28"] is parameter
                and handle.FieldsValue["ff0"] is sketch and handle.FieldsValue["ff8"] == slot
                and fields["f850"][0]["o"] is handle and fields["f1014"] in (0, 0x800),
                "decoded display does not retain its real ordered value and handle")
        actual[driver.NameValue] = {
            "intent": {"text_point_m": point(fields["f6a0"]["f38"]), "route_centerline": bool(fields["f1014"])},
            "witness": {
                "along_fraction": fields["f8a8"], "away_m": fields["f8b0"],
                "along_axis": point(fields["fa38"]), "away_axis": point(fields["f880"]),
                "start_m": point(fields["f958"]), "repeated_start_m": point(fields["f970"]),
                "end_m": point(fields["f988"]), "repeated_end_m": point(fields["f9a0"]),
                "length_m": fields["fad0"],
            },
            "owner": {"sketch_index": sketch.IndexValue, "value_id": value.FieldsValue["f50"],
                      "display_id": fields["f58"], "group_slot": slot, "handle_index": handle.IndexValue,
                      "value_index": value.IndexValue, "parameter_index": parameter.IndexValue,
                      "display_index": display.IndexValue, "selected_point_indices": driver.PointValues,
                      "driving_value_m": driver.MetresValue},
        }
    require(tuple(actual) == ("D1", "D2"), "decoded child has a different driver order")
    require(all(len({row["owner"][key] for row in actual.values()}) == 2
                for key in ("value_id", "display_id", "value_index", "display_index", "handle_index", "parameter_index")),
            "decoded rectangle label roles collide across their distinct owners")
    config_bytes, config = WriteConfigMut(link.ConfigValue.RootValue, 19000, link.ConfigValue.HeaderValue)
    resolved_bytes, _ = WriteResolMut(link.ResolvedValue.RootsValue, link.ResolvedValue.ExtraFields,
                                       19000, config.MapValue, link.ResolvedValue.ContextValue)
    require(config_bytes == child.streams[CONFIG] and resolved_bytes == child.streams[RESOLVED],
            "the linked typed ownership streams must reserialize exactly")
    return {"parent": artifact(bundle), "child": artifact(bundle.ChildValue), "actual": actual,
            "linked_round_trips": [CONFIG, RESOLVED]}


def worker():
    bind(ROOT)
    from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

    audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
    sys.addaudithook(audit.InspectEvent)
    from convert.adapters.solidworks.Core.AssemblyPreparation.PrepareAssembly import PrepareAssembly
    from interchange.serialization.Deserialize import FromData
    from SketchLabelIntent import make_group
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadLineDims import ReadLineDims
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from RectanglePresentation import point

    payload = json.load(sys.stdin)
    require(set(payload) == {"document", "labels", "native_parent", "event"} and payload["event"] == EVENT,
            "the guarded worker requires only the neutral document and exact authored label payload")
    document = FromData(payload["document"])
    for module in (
        "interchange.document.Behavior.DocumentIo", "interchange.document.Models.DocumentProvenance",
        "interchange.document.Validation.DocumentValidate", "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate", "interchange.document.Validation.DocumentReferenceValidate",
    ):
        import_module(module)
    for name in ("utf-16-le", "utf-8", "utf-8-sig", "latin-1", "ascii"):
        lookup(name)
    document.assert_valid()
    try:
        audit.BeginBuild()
        if payload["labels"] is None:
            bundle = PrepareAssembly(document, payload["native_parent"], payload["event"])
        else:
            bundle = make_group(document, payload["native_parent"], payload["event"], payload["labels"])
        result = {"passed": True, **audit_link(bundle)}
    except (ValueError, TypeError, PermissionError) as error:
        result = {"passed": False, "exception": type(error).__name__, "error": str(error)}
    cad = [name for name in sys.modules if name == "Swapp" or name == "pythoncom" or name.startswith("win32com")]
    runtime_research = sorted(name for name, module in tuple(sys.modules.items())
                              if str(getattr(module, "__file__", "")).startswith(str(ROOT / "re") + "/")
                              and name not in {"__main__", "PlanarRegistryBuild", "SketchLabelIntent",
                                               "SpatialTextMut", "RectanglePresentation"})
    require(not cad and not runtime_research and not audit.DeniedReads,
            "the research worker crossed its declared input or execution boundary: " + repr(audit.DeniedReads))
    return {**result, "pid": os.getpid(), "runtime_input_reads": 0, "cad_imports": []}


def fixture(dimensions, *, translated=False):
    from MakeAssemblyBoundaryCase import dimensioned_child, make_case
    from interchange.geometry.Models.VectorSpace import SpaceVector

    parent = make_case(2)
    graph = parent.assembly
    link, = graph.documents
    original = link.document
    profile = original.sketches[0]
    child = dimensioned_child(original.metadata["name"], dimensions, original.configurations[0].name)
    planes = original.support_planes
    if translated:
        front = planes[2]
        planes = (*planes[:2], replace(front, transform=replace(front.transform, origin=SpaceVector(1., 0., 0.))))
    child = replace(child, support_planes=planes,
                    sketches=(replace(child.sketches[0], support_plane_id=profile.support_plane_id),))
    return replace(parent, assembly=replace(graph, documents=(replace(link, document=child),)))


def label_rows(child, points, routing):
    sketch, = child.sketches
    return [{"sketch_id": sketch.id, "parameter_id": identity, "text_point_m": xyz, "route_centerline": route}
            for identity, xyz, route in zip(sketch.parameter_ids, points, routing, strict=True)]


def edge_points(entity):
    return tuple([point.x * .001, point.y * .001, 0.] for point in (entity.geometry.start, entity.geometry.end))


def defaults(child):
    first, right = edge_points(child.sketches[0].entities[0])
    _, top = edge_points(child.sketches[0].entities[1])
    return ([(first[0] + right[0]) / 2, first[1] - (top[1] - first[1]) / 4, 0.],
            [right[0] + (right[0] - first[0]) / 4, (first[1] + top[1]) / 2, 0.])


def predict(child, labels):
    sketch, = child.sketches
    intended = {row["parameter_id"]: row for row in labels}
    by_driver = {row.id: row.name for row in child.parameters}
    result = {}
    for key, edge in zip(sketch.parameter_ids, sketch.entities[:2], strict=True):
        row = intended[key]
        start, end = edge_points(edge)
        dx, dy = (end[index] - start[index] for index in (0, 1))
        length = hypot(dx, dy)
        u, v = dx / length, dy / length
        x, y, z = row["text_point_m"]
        px, py = x - start[0], y - start[1]
        result[by_driver[key]] = {
            "intent": {"text_point_m": [x, y, z], "route_centerline": row["route_centerline"]},
            "witness": {
                "along_fraction": (px * u + py * v) / length, "away_m": px * v - py * u,
                "along_axis": [u, v, 0.], "away_axis": [v, -u, 0.],
                "start_m": start, "repeated_start_m": start, "end_m": end, "repeated_end_m": end,
                "length_m": length,
            },
        }
    return result


def confirm(actual, expected):
    require(tuple(actual) == tuple(expected), "predicted and decoded parameter ID roles differ")
    for key, row in actual.items():
        candidate = expected[key]
        require(row["intent"] == candidate["intent"], "decoded label point or routing differs: " + key)
        require(isclose(row["owner"]["driving_value_m"], candidate["witness"]["length_m"], rel_tol=0, abs_tol=1e-14),
                "the selected live value does not measure the authored edge: " + key)
        require(set(row["witness"]) == set(candidate["witness"]), "decoded witness roles differ: " + key)
        for field, want in candidate["witness"].items():
            seen = row["witness"][field]
            numbers = zip(seen, want, strict=True) if type(want) is list else ((seen, want),)
            require(all(isclose(a, b, rel_tol=0, abs_tol=1e-14) for a, b in numbers),
                    "independently predicted witness differs: " + key + " " + field)


def payload(document, labels):
    from interchange.serialization.EncodeData import ToData

    path = PureWindowsPath("C:/KitSketchLabelIntent") / (document.metadata["name"] + ".SLDASM")
    return {"document": ToData(document), "labels": labels, "native_parent": str(path), "event": EVENT}


def send(request):
    raw = (json.dumps(request, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    process = run((sys.executable, "-I", "-B", str(HERE), "worker"), input=raw,
                  capture_output=True, check=False, timeout=90)
    require(process.returncode == 0, process.stderr.decode(errors="replace"))
    data = json.loads(process.stdout)
    require(data["runtime_input_reads"] == 0 and data["cad_imports"] == [] and data["pid"] != os.getpid(),
            "the guarded worker did not run independently")
    return data, fingerprint(raw)["sha256"], fingerprint(process.stdout)["sha256"]


def contrast_document(dimensions, xy, depths):
    document = fixture(dimensions)
    child = document.assembly.documents[0].document
    ordinary = label_rows(child, defaults(child), (False, False))
    planar = tuple([*pair, 0.] for pair in xy)
    spatial = tuple([*pair, depth] for pair, depth in zip(xy, depths, strict=True))
    labels = {
        "explicit-default": ordinary,
        "xy-only": label_rows(child, planar, (False, False)),
        "xyz": label_rows(child, spatial, (False, False)),
        "width-route": list(reversed(label_rows(child, spatial, (True, False)))),
        "height-route": label_rows(child, spatial, (False, True)),
        "both-route": label_rows(child, spatial, (True, True)),
    }
    expected = {name: predict(child, value) for name, value in {"default": ordinary, **labels}.items()}
    requests = {name: payload(document, label) for name, label in {"default": None, **labels}.items()}
    return document, labels["xyz"], requests, expected


def changed(first, second):
    require(first.keys() == second.keys(), "an annotation edit changed the stream census")
    return [key for key in first if first[key] != second[key]]


def evidence(first, second, request, oracle):
    result, request_sha, stdout = first
    replay, replay_sha, replay_stdout = second
    pid, replay_pid = result["pid"], replay["pid"]
    require(pid != replay_pid and request_sha == replay_sha and result["passed"] and replay["passed"]
            and {key: val for key, val in replay.items() if key != "pid"}
            == {key: val for key, val in result.items() if key != "pid"},
            "complete guarded bundle or typed readback is nondeterministic")
    confirm(result["actual"], oracle)
    return {**result, "request_sha256": request_sha, "stdout_sha256": [stdout, replay_stdout],
            "worker_pids": [pid, replay_pid], "submitted_labels": request["labels"]}


def negatives(document, base):
    from copy import deepcopy

    requests = {}
    for name, key, value, message in (
        ("crossed-sketch", "sketch_id", "unowned/sketch", "actual unique driving parameter and sketch"),
        ("same-driver-twice", "parameter_id", base[1]["parameter_id"], "actual unique driving parameter and sketch"),
        ("foreign-driver", "parameter_id", document.parameters[0].id, "actual unique driving parameter and sketch"),
        ("implicit-routing", "route_centerline", 1, "requires an explicit boolean"),
        ("short-point", "text_point_m", [0., 0.], "requires three explicit world coordinates"),
        ("boolean-coordinate", "text_point_m", [0., -.023174, True], "finite numbers without booleans"),
        ("outside-witness-span", "text_point_m", [1., -.023174, .0072], "must lie outside beside its dimensioned edge"),
    ):
        bad = deepcopy(base)
        bad[0][key] = value
        requests[name] = (payload(document, bad), message)
    translated = fixture((.0473, .0289, .0117), translated=True)
    requests["translated-front"] = (payload(translated, base), "canonical principal frame at origin")
    return requests


def prove(output):
    bind(ROOT)
    modified = check_output(("git", "diff", "--name-only", BASE, "--", "src", "tests", "re/tooling/sw2026"),
                            cwd=ROOT, text=True).splitlines()
    require(set(modified) <= {str(path.relative_to(ROOT)) for path in (HERE, BUILDER)},
            "the comparison requires the exact unchanged base SDK and research dependencies")
    require(not output.exists() and not output.is_relative_to(ROOT),
            "choose an unused proof receipt outside the checkout")
    designs = {
        "rectangle-wide": contrast_document((.0473, .0289, .0117), ((-.00637, -.023174), (.033987, .004283)),
                                             (.000371, -.000613)),
        "rectangle-tall": contrast_document((.0317, .0423, .00831), ((.007883, -.031059), (.028571, -.006127)),
                                             (-.000457, .000829)),
    }
    jobs = {(design, variant): request for design, (_, _, inputs, _) in designs.items() for variant, request in inputs.items()}
    first, labels, *_ = designs["rectangle-wide"]
    denied = negatives(first, labels)
    result = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        running = {key: [pool.submit(send, request) for _ in range(2)] for key, request in jobs.items()}
        rejected = {name: pool.submit(send, request) for name, (request, _) in denied.items()}
        for (design, variant), pair in running.items():
            result.setdefault(design, {})[variant] = evidence(
                *(job.result() for job in pair), jobs[design, variant], designs[design][3][variant])
        refused = {}
        for key, job in rejected.items():
            data, request_hash, stdout = job.result()
            require(data["passed"] is False and "child" not in data and denied[key][1] in data["error"],
                    "unqualified input did not refuse at the expected boundary: " + key)
            refused[key] = {**data, "request_sha256": request_hash, "stdout_sha256": stdout}
    for design, entries in result.items():
        control = entries["default"]
        identities = {key: row["owner"] for key, row in control["actual"].items()}
        for name, row in entries.items():
            require(row["parent"] == control["parent"] and identities == {key: part["owner"] for key, part in row["actual"].items()},
                    "text intent changed the linked parent or actual driver/display identities")
            row["changed_child_streams"] = changed(control["child"]["streams"], row["child"]["streams"])
            unique = name not in ("default", "explicit-default")
            require(row["changed_child_streams"] == ([RESOLVED] if unique else [])
                    and (row["child"] != control["child"]) is unique,
                    "text contrast must change only the resolved stream and preserve explicit default bytes")
        planar_witness = {key: row["witness"] for key, row in entries["xy-only"]["actual"].items()}
        for variant in ("xyz", "width-route", "height-route", "both-route"):
            actual_witness = {key: row["witness"] for key, row in entries[variant]["actual"].items()}
            require(actual_witness == planar_witness,
                    "normal offset or centreline routing must preserve authored XY witnesses exactly")
        require(len({row["child"]["sha256"] for row in entries.values()}) == len(entries) - 1,
                "XYZ or independent routing did not materially select distinct stored output: " + design)
    pids = [pid for rows in result.values() for row in rows.values() for pid in row["worker_pids"]]
    pids += [row["pid"] for row in refused.values()]
    require(len(pids) == len(set(pids)), "guarded observations share a process")
    source = {
        path.relative_to(ROOT).as_posix(): fingerprint(path.read_bytes())["sha256"]
        for path in (HERE, BUILDER, HERE.with_name("PlanarRegistryBuild.py"), HERE.with_name("RectanglePresentation.py"),
                     HERE.parent.parent / "SpatialTextMut.py", HERE.parent.parent / "MakeAssemblyBoundaryCase.py",
                     ROOT / "tests/Convert/Solidworks/Research/ConstructionGuard.py")
    }
    receipt = {
        "schema": "kit.sw2026.planar-sketch-label-intent-host.v1",
        "base_revision": BASE, "base_sdk_tree": check_output(("git", "rev-parse", BASE + ":src"), cwd=ROOT, text=True).strip(),
        "source_sha256": source, "event": EVENT, "interpreter": sys.version,
        "interpreter_sha256": fingerprint(Path(sys.executable).read_bytes())["sha256"],
        "guarded_workers": len(pids), "native_processes": 0, "runtime_input_reads": 0,
        "typed_linked_round_trips": sum(len(row["linked_round_trips"]) * 2 for rows in result.values() for row in rows.values()),
        "prior_source_inputs_read": 0, "new_heldout_credit": 0, "source_admission": False, "native_acceptance": False,
        "cases": result, "refusals": refused,
    }
    return {"passed": True, "receipt_sha256": write(output, receipt), "guarded_workers": len(pids),
            "typed_linked_round_trips": receipt["typed_linked_round_trips"], "native_processes": 0}


def main():
    parser = ArgumentParser()
    parser.add_argument("mode", choices=("prove", "worker"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    require(args.mode == "worker" or args.output is not None, "proof requires a new report destination")
    result = worker() if args.mode == "worker" else prove(args.output.resolve())
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
