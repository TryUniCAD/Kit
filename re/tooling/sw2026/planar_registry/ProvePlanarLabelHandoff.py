from argparse import ArgumentParser
from codecs import lookup
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import replace
from importlib import import_module
from io import BytesIO
import json
import os
from pathlib import Path
from subprocess import check_output, run
import sys
from tarfile import open as open_tar
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from PlanarRegistryBuild import ROOT, bind, fingerprint, require, write
from ProveSketchLabelIntent import RESOLVED, audit_link, changed, confirm, defaults, fixture, label_rows, payload, predict

BASE = "fecc574bad42189dbbc2c66c997b7e71e9005972"
PLAN = "convert.adapters.solidworks.Core.AssemblyPreparation"
WIDE = ((.05175, .036125, .010875), ((-.00815, -.02685, .000293), (.03529, .00473, -.000711)), (True, False))
TALL = ((.028375, .045625, .013125), ((.004872, -.03411, -.000392), (.02398, -.00729, .000908)), (False, True))


def worker(mode, baseline):
    bind(ROOT)
    if mode == "baseline":
        require(baseline is not None, "the legacy comparison requires exact base source")
        baseline = baseline.resolve()
        sys.path.insert(0, str(baseline / "src"))
    from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

    audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
    if mode == "baseline":
        audit.SourceDir = baseline / "src"
    sys.addaudithook(audit.InspectEvent)
    from convert.adapters.solidworks.Core.AssemblyWriting.CanWriteAsm import CanWriteAsm
    from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadLineDims import ReadLineDims
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from interchange.serialization.Deserialize import FromData
    from RectanglePresentation import point

    package = import_module(PLAN + ".PrepareAssembly")
    if mode == "research":
        from SketchLabelIntent import make_group
    if mode == "current":
        kind = import_module(PLAN + ".Children.SketchLabelIn").SketchLabelIn
    request = json.load(sys.stdin)
    require(set(request) == {"document", "labels", "native_parent", "event"}, "unexpected guarded request fields")
    doc = FromData(request["document"])
    for module in (
        "interchange.document.Behavior.DocumentIo", "interchange.document.Models.DocumentProvenance",
        "interchange.document.Validation.DocumentValidate", "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate", "interchange.document.Validation.DocumentReferenceValidate",
    ):
        import_module(module)
    for codec in ("utf-8", "utf-8-sig", "utf-16-le", "latin-1", "ascii"):
        lookup(codec)
    prepared_children = 0
    original = package.MakeRectDimPart

    def observe_child(*args):
        nonlocal prepared_children
        prepared_children += 1
        return original(*args)

    package.MakeRectDimPart = observe_child
    doc.assert_valid()
    audit.BeginBuild()
    registry_target = Path(doc.metadata["name"] + ".SLDASM")
    eligible = CanWriteAsm(doc, registry_target)
    try:
        rows = request["labels"]
        args = (doc, request["native_parent"], request["event"])
        if mode == "research":
            bundle = make_group(*args, rows)
        elif mode == "baseline" or rows is None:
            require(rows is None, "the legacy comparison accepts only the ordinary default")
            bundle = package.PrepareAssembly(*args)
        else:
            labels = tuple(kind(row["sketch_id"], row["parameter_id"], tuple(row["text_point_m"]), row["route_centerline"])
                           for row in rows)
            bundle = package.PrepareAssembly(*args, SketchLabels=labels)
        result = {"passed": True, **audit_link(bundle)}
    except (ValueError, TypeError, PermissionError) as error:
        result = {"passed": False, "error": str(error)}
    native_modules = [name for name in sys.modules if name in ("Swapp", "pythoncom") or name.startswith("win32com")]
    require(not native_modules and not audit.DeniedReads, "guarded worker crossed its authoring boundary")
    return {**result, "pid": os.getpid(), "runtime_reads": len(audit.DeniedReads), "native_imports": native_modules,
            "prepared_children": prepared_children, "ordinary_registry_eligible": eligible}


def probe(request, mode, baseline):
    raw = (json.dumps(request, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()
    command = [sys.executable, "-I", "-B", str(HERE), "worker", "--mode", mode]
    if mode == "baseline":
        command.extend(("--baseline", str(baseline)))
    call = run(command, input=raw, capture_output=True, timeout=120, check=False)
    require(call.returncode == 0, call.stderr.decode(errors="replace"))
    result = json.loads(call.stdout)
    require(result["pid"] != os.getpid() and not result["runtime_reads"] and not result["native_imports"],
            "the archive proof did not run at an independent guarded boundary")
    return result | {"request_sha256": fingerprint(raw)["sha256"]}


def variants(dimensions, points, routes):
    doc = fixture(dimensions)
    child = doc.assembly.documents[0].document
    default = label_rows(child, defaults(child), (False, False))
    xy = label_rows(child, tuple([x, y, 0.0] for x, y, _ in points), (False, False))
    xyz = list(reversed(label_rows(child, points, routes)))
    requests = {"baseline": (payload(doc, None), "baseline"), "default": (payload(doc, None), "current"),
                "explicit_default": (payload(doc, default), "current"), "planar": (payload(doc, xy), "current"),
                "spatial": (payload(doc, xyz), "current"), "repeat": (payload(doc, xyz), "current"),
                "research": (payload(doc, xyz), "research")}
    expected = {"baseline": default, "default": default, "explicit_default": default, "planar": xy,
                "spatial": xyz, "repeat": xyz, "research": xyz}
    return doc, xyz, requests, {name: predict(child, rows) for name, rows in expected.items()}


def refusals(doc, labels, dimensions):
    from interchange.Records.RecordDiagnostic import Diagnostic

    bad = {}
    for name, key, value, error in (
        ("foreign_sketch", "sketch_id", "unowned/sketch", "both actual owned sketch drivers"),
        ("duplicate_driver", "parameter_id", labels[1]["parameter_id"], "both actual owned sketch drivers"),
        ("parent_driver", "parameter_id", doc.parameters[0].id, "both actual owned sketch drivers"),
        ("short_point", "text_point_m", [0.0, 0.0], "three finite sketch frame coordinates"),
        ("boolean_point", "text_point_m", [0.0, .03, True], "real numeric value"),
        ("implicit_route", "route_centerline", 1, "routing requires an explicit boolean"),
        ("outside_witness", "text_point_m", [.5, .5, .002], "outside beside its dimensioned edge"),
    ):
        altered = deepcopy(labels)
        altered[0][key] = value
        bad[name] = payload(doc, altered), error
    bad["missing_driver"] = payload(doc, labels[:1]), "two typed sketch labels"
    bad["shifted_support"] = (payload(fixture(dimensions, translated=True), labels), "canonical principal frame at origin")
    guarded = replace(doc, diagnostics=(Diagnostic("disclosed.unprojected_record", "explicit neutral reader boundary"),))
    bad["unprojected_root"] = payload(guarded, labels), "root contains unprojected model content"
    return bad


def verify_design(results, expected):
    ordinary = results["default"]
    owners = {name: row["owner"] for name, row in ordinary["actual"].items()}
    for name, row in results.items():
        require(row["passed"] and row["ordinary_registry_eligible"], "eligible neutral design failed: " + name)
        require(row["prepared_children"] == (0 if name == "research" else 1), "the checked planner did not build the owned child")
        confirm(row["actual"], expected[name])
        require(row["parent"] == ordinary["parent"] and owners == {key: value["owner"] for key, value in row["actual"].items()},
                "label authoring changed linked parent bytes or actual child dimension identity")
    require(all(results[name]["child"] == ordinary["child"] for name in ("baseline", "explicit_default")),
            "legacy or explicit default label preparation changed its bytes")
    spatial = results["spatial"]
    require(all(results[name]["child"] == spatial["child"] for name in ("repeat", "research")),
            "shared typed handoff differs from a repeated build or the previous modelled constructor")
    for label in ("planar", "spatial"):
        require(changed(ordinary["child"]["streams"], results[label]["child"]["streams"]) == [RESOLVED],
                "the authored labels changed more than the child's resolved display owners")
    require(changed(results["planar"]["child"]["streams"], spatial["child"]["streams"]) == [RESOLVED]
            and all(row["witness"] == results["planar"]["actual"][name]["witness"] for name, row in spatial["actual"].items()),
            "spatial labels or route choices changed the derived planar witnesses")


def prove(output):
    bind(ROOT)
    require(output.is_absolute() and not output.exists() and not output.is_relative_to(ROOT), "use a fresh host evidence path")
    designs = {key: variants(*values) for key, values in (("wide", WIDE), ("tall", TALL))}
    source, labels, _, _ = designs["wide"]
    negative = refusals(source, labels, WIDE[0])
    results, refused = {}, {}
    with TemporaryDirectory(prefix="KitPlanarLabelBaseline-") as root:
        baseline = Path(root)
        code = check_output(("git", "archive", BASE, "src"), cwd=ROOT)
        with open_tar(fileobj=BytesIO(code), mode="r:") as tracked:
            tracked.extractall(baseline, members=(row for row in tracked.getmembers() if row.isfile() and row.name.endswith(".py")), filter="data")
        with ThreadPoolExecutor(max_workers=4) as pool:
            pending = {key: {name: pool.submit(probe, request, mode, baseline) for name, (request, mode) in requests.items()}
                       for key, (_, _, requests, _) in designs.items()}
            rejected = {name: pool.submit(probe, request, "current", baseline) for name, (request, _) in negative.items()}
            for key, jobs in pending.items():
                results[key] = {name: item.result() for name, item in jobs.items()}
                verify_design(results[key], designs[key][3])
            for name, outcome in rejected.items():
                row = outcome.result()
                require(not row["passed"] and row["prepared_children"] == 0 and negative[name][1] in row["error"],
                        "unqualified display intent reached the owning child constructor: " + name)
                refused[name] = row
    require(not refused["unprojected_root"]["ordinary_registry_eligible"], "ordinary eligibility no longer refuses the root control")
    workers = [row for design in results.values() for row in design.values()] + list(refused.values())
    require(len({row["pid"] for row in workers}) == len(workers), "guarded outcomes reused a process")
    return write(output, {"schema": "kit.sw2026.planar-label-shared-handoff.v1", "base": BASE,
                          "processes": len(workers), "independently_authored_models": len(designs), "designs": results,
                          "refusals": refused, "reserved_sources_read": 0, "native_processes": 0, "heldout_credit": 0})


def smoke():
    bind(ROOT)
    source, labels, inputs, expected = variants(*WIDE)
    controls = {name: probe(*inputs[name], None) for name in ("default", "spatial")}
    bad, message = refusals(source, labels, WIDE[0])["duplicate_driver"]
    denied = probe(bad, "current", None)
    require(all(row["passed"] and row["prepared_children"] == 1 for row in controls.values())
            and not denied["passed"] and denied["prepared_children"] == 0 and message in denied["error"],
            "the public-default and explicit planning processes did not preserve the owner gate")
    default, spatial = (controls[name] for name in ("default", "spatial"))
    confirm(spatial["actual"], expected["spatial"])
    streams = changed(default["child"]["streams"], spatial["child"]["streams"])
    require(default["parent"] == spatial["parent"] and streams == [RESOLVED]
            and all(row["owner"] == default["actual"][name]["owner"] for name, row in spatial["actual"].items()),
            "explicit labels disturbed default parent bytes or real driver ownership")
    require(len({default["pid"], spatial["pid"], denied["pid"]}) == 3, "queue smoke requires distinct guarded processes")
    return {"pass": True, "guarded_workers": 3, "runtime_input_reads": 0, "changed_child_streams": streams}


def main():
    args = ArgumentParser()
    args.add_argument("role", choices=("worker", "prove", "smoke"))
    args.add_argument("--mode", choices=("baseline", "research", "current"), default="current")
    args.add_argument("--baseline", type=Path)
    args.add_argument("--output", type=Path)
    values = args.parse_args()
    if values.role == "worker":
        print(json.dumps(worker(values.mode, values.baseline), sort_keys=True, allow_nan=False))
    elif values.role == "smoke":
        print(json.dumps(smoke(), sort_keys=True))
    else:
        print(prove(values.output))


if __name__ == "__main__":
    main()
