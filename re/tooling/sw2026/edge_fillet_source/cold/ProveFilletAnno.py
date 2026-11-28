from argparse import ArgumentParser
from json import dumps, loads
from pathlib import Path
from subprocess import run
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from BuildColdFillet import GUEST_ROOT, HERE, INTENT_PIN, ROOT, launch, sha
from ColdFilletAnno import read_annotation_binding
from ColdFilletWire import VERSION, read_cold_resolved, write_cold_resolved
from FilletModel import require
from ProveFilletInputs import guard, pinned

from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KResolvedFeaturesStream
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

MEASUREMENTS = ROOT / "re/solidworks/measurements/2026"
SOURCE_DIGEST = "e7573a71c5fb709a26ae512a332f3fe6eecca5fef949b8f98380ac7cbd1337f3"
BASELINE_DIGEST = "efe553717fcd7ea1323bd58c138a5a9211f4b022870fdd89d3807f987c8ae8dc"
CONFIG = "Contents/Config-0"
TOP = {"name": "*Top", "basis": [[1.0, 0.0, 0.0], [0.0, 0.0, -1.0], [0.0, 1.0, 0.0]]}
BACK = {"name": "*Back", "basis": [[-1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, -1.0]]}
LEFT = {"name": "*Left", "basis": [[0.0, 0.0, 1.0], [0.0, 1.0, 0.0], [-1.0, 0.0, 0.0]]}
FRONT = {"name": "*Front", "basis": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]}


def read_catalog(config, roots):
    root = config.RootValue
    (fillet,) = (node for node in roots if node and node.ClassValue.NameValue == "Fillet_c")
    (item,) = fillet.FieldsValue["f868"].FieldsValue["items"]
    display = item["o"].FieldsValue["f08"]
    fields = root.FieldsValue
    catalogue = fields["fa48"].FieldsValue
    views = []
    for row in catalogue["items"]:
        owner = row["o"]
        matches = [entry for entry in config.MapValue.EntriesValue if entry.EntryValue is owner]
        require(len(matches) == 1 and matches[0].IndexValue == owner.IndexValue,
                "fillet annotation view must own its actual inherited Config-0 slot")
        typed = owner.FieldsValue
        transform = typed["f368"]
        matrix = transform.get("f08", {})
        basis = [[matrix[f"m{3 * row + column}"] for row in range(3)] for column in range(3)] if matrix else FRONT["basis"]
        require(transform["has_matrix"] == int(bool(matrix))
                and tuple(transform[key] for key in ("f58", "f60", "f68", "f70", "f78")) == (0.0, 0.0, 0.0, 1.0, 0),
                "fillet proof supports unshifted annotation frames")
        views.append({"name": typed["f358"], "basis": basis, "id": typed["f360"], "map_slot": owner.IndexValue})
    require(catalogue["n"] == len(views) and fields["nec8"] == len(fields["fec0"]),
            "fillet annotation count differs from its modeled owner rows")
    return {"catalogue": views, "active": fields["feb4"], "frontier": fields["feb0"],
            "shown": [row["v"] for row in fields["fec0"]], "driver": read_annotation_binding(root, display)}


def worker(raw, saved):
    attempts = guard()
    archive = SldprtArchive.from_bytes(raw)
    if saved:
        link = ReadNativeLink(archive, 0, ReadFillets=True)
        config, roots = link.ConfigValue, link.ResolvedValue.RootsValue
    else:
        header = ReadHeaderGraph(archive.require(CONFIG + "-ModelHeader"), VERSION)
        config = ReadConfigMut(archive.require(CONFIG), VERSION, header)
        resolved = archive.require(KResolvedFeaturesStream)
        roots, _, _ = read_cold_resolved(resolved, config.MapValue)
        replay, _, _ = write_cold_resolved(roots, config.MapValue, {"n": 0, "fcd8": []})
        require(replay == resolved, "annotated cold ResolvedFeatures did not exactly replay")
    data, typed = WriteConfigMut(config.RootValue, VERSION, config.HeaderValue)
    require(data == archive.require(CONFIG) and config.MapValue == typed.MapValue,
            "fillet annotation Config-0 did not exactly replay")
    result = read_catalog(config, roots)
    require(not attempts, "fillet annotation reader attempted external access")
    print(dumps(result | {"sha256": sha(raw), "config_sha256": sha(data), "config_map_next": config.MapValue.CounterValue,
                          "runtime_external_access_attempts": len(attempts)}, sort_keys=True, allow_nan=False))


def read_result(raw, mode):
    result = run((sys.executable, "-I", "-B", __file__, "--worker", mode), input=raw,
                 capture_output=True, cwd=ROOT, timeout=60, check=False)
    require(result.returncode == 0 and not result.stderr, result.stderr.decode(errors="replace"))
    value = loads(result.stdout)
    require(value["sha256"] == sha(raw), "fillet annotation reader input digest differs")
    return value


def authored(views, driver, active=None, shown=(None,)):
    return {"views": views, "driver_view": driver, "active_view": active, "shown_views": list(shown)}


def require_semantics(value, intent):
    slots = {item["name"]: 200 + index for index, item in enumerate(intent["views"])}
    require(value["catalogue"] and [(row["name"], row["basis"], row["id"]) for row in value["catalogue"]]
            == [(row["name"], row["basis"], slots[row["name"]]) for row in intent["views"]], "fillet view catalogue differs")
    require(value["frontier"] == max(slots.values())
            and value["active"] == slots.get(intent["active_view"], 199)
            and value["shown"] == sorted(slots.get(name, 199) for name in intent["shown_views"])
            and value["driver"] == {"name": intent["driver_view"], "id": slots[intent["driver_view"]]},
            "fillet annotation joins the wrong output owner")


def disclose(capture, expectations):
    receipt = loads(pinned(MEASUREMENTS / "EdgeFilletArchiveRead01.json", SOURCE_DIGEST))
    results = {}
    for row in receipt["results"]:
        name = row["case"]
        phase = name + ("Edited" if row["edited"] else "")
        raw = pinned(capture / name / (phase + ".SLDPRT"), row["source_sha256"])
        facts = read_result(raw, "saved")
        require_semantics(facts, expectations[name])
        results[phase] = facts
    return results


def measure(case, previous, match, independent):
    request = {key: value for key, value in case.items() if key != "edit_radius_mm"}
    _, baseline = launch(request, GUEST_ROOT)
    _, prior_edit = launch(request | {"radius_mm": case["edit_radius_mm"]}, GUEST_ROOT)
    require(baseline["sha256"] == previous["sha256"] and prior_edit["sha256"] == previous["radius_only"]["sha256"]
            and baseline["owners"] == previous["owners"] and baseline["streams"] == previous["streams"],
            "absent annotation changed a previously proved neutral fillet")
    outputs = {}
    for label, intent in (("source_orientation", request | {"annotations": match}),
                          ("independent_neutral", request | independent)):
        data, witness = launch(intent, GUEST_ROOT)
        require((data, witness) == launch(intent, GUEST_ROOT), "fileless fillet annotation writes disagree")
        observed = read_result(data, "cold")
        require_semantics(observed, intent["annotations"])
        require(observed["driver"] == witness["owners"]["annotation"] and observed["runtime_external_access_attempts"] == 0,
                "guarded fillet annotation read and write disagree")
        outputs[label] = {"intent_sha256": sha(dumps(intent, sort_keys=True).encode()), "read": observed, "generated": witness}
    only_changes = {key for key, value in outputs["source_orientation"]["generated"]["streams"].items()
                    if baseline["streams"].get(key) != value}
    require(only_changes == {CONFIG, KResolvedFeaturesStream}, "annotation-only intent changed unrelated fillet streams")
    return {"baseline_sha256": baseline["sha256"], "baseline_edit_sha256": prior_edit["sha256"],
            "annotation_only_changed_streams": sorted(only_changes), **outputs}


def refusals(case, match):
    request = {key: value for key, value in case.items() if key != "edit_radius_mm"}
    top, back = match["views"]
    wrong_orientation = top | {"basis": [[1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [0.0, 1.0, 0.0]]}
    contrasts = {
        "missing_driver": (match | {"driver_view": "Omitted"}, "absent from its catalogue"),
        "duplicate_view": (match | {"views": [top, back, back]}, "ambiguous authored annotation view names"),
        "unknown_shown": (match | {"shown_views": ["Omitted"]}, "names no registered view"),
        "left_handed": (match | {"views": [wrong_orientation, back]}, "right-handed model-axis rotation"),
    }
    observed = {}
    for name, (spec, expected) in contrasts.items():
        failure = launch(request | {"annotations": spec}, GUEST_ROOT, expect_success=False)
        require(expected in failure, "fillet annotation refusal missed its expected guard")
        observed[name] = failure
    return observed


def main():
    parser = ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--worker", choices=("saved", "cold"))
    modes.add_argument("--capture", type=Path)
    args = parser.parse_args()
    if args.worker:
        worker(sys.stdin.buffer.read(), args.worker == "saved")
        return
    cases = loads(pinned(HERE.parent.parent / "DisclosedFilletInputs.json", INTENT_PIN))["cases"]
    prior = loads(pinned(MEASUREMENTS / "EdgeFilletModelColdCompile01.json", BASELINE_DIGEST))
    expectations = {"EdgeFilletAxial": authored([TOP, BACK], "*Back"),
                    "EdgeFilletTransverse": authored([TOP, LEFT], "*Left")}
    independent = {"EdgeFilletAxial": {"center_mm": [2.25, -3.5], "size_mm": [41.0, 27.0, 15.0], "radius_mm": 3.25,
                                      "annotations": authored([BACK, TOP], "*Back", "*Top", (None, "*Back"))},
                   "EdgeFilletTransverse": {"center_mm": [-4.5, 8.5], "size_mm": [46.0, 29.0, 23.0], "radius_mm": 2.75,
                                           "annotations": authored([FRONT, TOP, LEFT], "*Left", "*Left", ("*Top", "*Left"))}}
    disclosed = disclose(args.capture, expectations)
    generated = {case["name"]: measure(case, prior["cases"][case["name"]], expectations[case["name"]], independent[case["name"]])
                 for case in cases}
    negative = refusals(cases[0], expectations[cases[0]["name"]])
    sources = {path.name: sha(path.read_bytes()) for path in sorted(HERE.parent.glob("*.py"))}
    print(dumps({"schema": "kit.sw2026.fillet-explicit-annotation-ownership.v1", "sdk_base": "f835b1395a6e0159e2e08ae45d26a3239e0151ed",
                 "native_source_build": "34.5.2.0604", "source_archive_receipt_sha256": SOURCE_DIGEST,
                 "reference_model_receipt_sha256": BASELINE_DIGEST, "neutral_stock_sha256": INTENT_PIN,
                 "tools_sha256": sources, "disclosed": disclosed, "generation": generated, "refusals": negative,
                 "guarded_data_processes": 24, "native_processes_started": 0, "native_acceptance_added": 0,
                 "heldout_inputs_read": 0, "public_writer_changed": False}, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
