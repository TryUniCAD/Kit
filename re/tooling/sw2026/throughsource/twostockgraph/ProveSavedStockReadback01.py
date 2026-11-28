from argparse import ArgumentParser
from hashlib import sha256
from importlib import import_module
from pathlib import Path
from subprocess import check_output, run
import codecs
import json
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
TOLERANCE = "e64e9a2713a152809968c610cee57699d58fb69b8c7bf016d63983464f5f6c0a"
ORIGINAL = "748cdbec3fe61d6801f3d606e64fe42ecba95e9a647897be3fe3790570a889f3"
GENERATED = "6eca4bed5c698744cb3f33f39b1f15aebb69bedfef658060ef7c1d3a8603a508"
NEGATIVE = ("retry", "update-version", "build-date", "first-stock", "cold")


def require(condition, diagnostic):
    if not condition:
        raise ValueError(diagnostic)


def pinned(path, digest):
    require(path.is_file() and not path.is_symlink(), "saved source is missing or redirected")
    source = path.read_bytes()
    require(sha256(source).hexdigest() == digest, "saved source checksum differs")
    return source


def decline(mode, raw):
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockOps import ReadStockOps
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockRoots import ReadStockRoots
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    link = ReadNativeLink(SldprtArchive.from_bytes(raw), 0)
    features = ReadStockRoots(link)
    _, first, _, second, _, _ = tuple(features.values())[-6:]
    if mode == "first-stock":
        first.FieldsValue["f838"] = 1e-5
    elif mode == "cold":
        second.FieldsValue.update(f838=1e-5, f2b8=19000, f2bc=2026306)
    else:
        field, value = {"retry": ("f838", 2.5e-5), "update-version": ("f2b8", 0),
                        "build-date": ("f2bc", 2026305)}[mode]
        second.FieldsValue[field] = value
    try:
        ReadStockOps(link, features, AllowSavedTolerance=mode != "cold")
    except ValueError as error:
        require(str(error) == "two stock lineage has an alternate profile or extrusion mode",
                "the altered word failed at an unexpected owner")
        return {"refused": str(error)}
    raise ValueError("unqualified saved tolerance reached the stock history")


def observe(mode, raw):
    from convert import open_document
    from interchange.Enums.EnumFeatures import BooleanOp
    from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
    from interchange.geometry.Models.Selection import SelectPathElem

    full = mode == "strict"
    document = open_document(raw, source_format="solidworks.sldprt", include_brep=full)
    require(not document.validate(), "the public SDK document is invalid")
    rows = {step.name: step for step in document.feature_timeline}
    first, second, cut = (rows[role] for role in ("SteadyStock", "MovingStock", "ThroughFeature"))
    typed = document.metadata["solidworks.typed_resolved_semantics"]
    body = typed.get("cut_body_dependency")
    depth = {parameter.id: parameter.value.value for parameter in document.parameters if parameter.name == "D1"}
    values = [depth[owner.parameter_ids[0]] for owner in (first, second)]
    if not full:
        require(
            document.brep is None and not document.brep_payloads
            and len(document.bodies) == 1 and body is None
            and all(not item.endswith(":stock-body") for item in cut.selection_ids),
            "the established no-B-rep compatibility route changed",
        )
        return {"d1_mm": values, "body_count": len(document.bodies), "has_brep": False}
    require(
        isinstance(first.definition, ExtrudeFeature)
        and isinstance(second.definition, ExtrudeFeature)
        and first.operation == second.operation == BooleanOp.KCreate
        and isinstance(cut.definition, ExtrudeFeature)
        and cut.definition.end_condition == ExtrudeEnd.KThroughAll
        and cut.operation == BooleanOp.KCutOperation
        and first.id in cut.input_feature_ids
        and document.brep is not None and len(document.brep.bodies) == len(document.bodies) == 2,
        "the public adapter did not retain both typed producers and the through cut",
    )
    (selected,) = tuple(
        selection for selection in document.selections
        if selection.id == cut.id + ":stock-body"
    )
    require(
        selected.id in cut.selection_ids
        and selected.path == (SelectPathElem("feature", first.id, "body"),)
        and {item.final_feature_id for item in document.bodies} == {second.id, cut.id}
        and {item.design_body_id for item in document.brep.bodies} == {item.id for item in document.bodies}
        and body["consumed_atom_id"] == 101 and body["untouched_atom_id"] == 102
        and body["result_atom_id"] == 103,
        "the public design, selector and kernel body identities differ",
    )
    return {
        "d1_mm": values, "row_count": len(document.feature_timeline),
        "selection_id": selected.id, "selection_producer": first.id,
        "body_owners": {item.name: item.final_feature_id for item in document.bodies},
        "brep_bodies": len(document.brep.bodies), "lineage": body,
    }


def worker(mode):
    sys.path[:0] = [str(ROOT / "src"), str(ROOT)]
    from convert.api.ApiContext import GetRegistry
    from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

    GetRegistry()
    for name in ("ascii", "latin-1", "utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be"):
        codecs.lookup(name)
    for module in ("DocumentAssemblyValidate", "DocumentFeatureValidate", "DocumentReferenceValidate"):
        import_module("interchange.document.Validation." + module)
    for module in ("DocumentProvenance", "DocumentWalk"):
        import_module("interchange.document.Models." + module)
    audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
    sys.addaudithook(audit.InspectEvent)
    raw = sys.stdin.buffer.read()
    result = decline(mode, raw) if mode in NEGATIVE else observe(mode, raw)
    require(not audit.DeniedReads, "saved stock read attempted runtime data-file access")
    return {**result, "sha256": sha256(raw).hexdigest(), "runtime_data_file_reads": len(audit.DeniedReads)}


def run_worker(mode, raw):
    result = run((sys.executable, "-I", "-B", str(HERE), "--worker", mode), input=raw,
                 capture_output=True, timeout=90)
    require(result.returncode == 0, result.stderr.decode())
    return json.loads(result.stdout)


def prove(workspace):
    implementation = {
        f"src/convert/adapters/solidworks/Core/TypedResolved/Cuts/MultiStock/{module}.py"
        for module in ("CheckStockMode", "ReadStockOps", "ReadTwoStockCut", "StockOpsMap")
    }
    source_sha256 = {name: sha256((ROOT / name).read_bytes()).hexdigest() for name in implementation}
    proof = ROOT / "re/solidworks/measurements/2026/TwoStockSaveTolerance01.json"
    contrast = json.loads(pinned(proof, TOLERANCE))
    previous = workspace / "GeneratedTwoStockGraph01"
    data = {"original": pinned(workspace / "ThroughMultiStock03/DisclosedNative/ThroughMultiStock.SLDPRT", ORIGINAL)}
    phases = contrast["phases"]
    data["moving"] = pinned(previous / "NativeAfterEdit.SLDPRT", phases["native_moving_edit"]["sha256"])
    for mode in ("Unchanged", "Selected"):
        case = contrast["native"]["derivatives"][mode]
        data[mode.lower()] = pinned(workspace / "TwoStockSaveContrast01" / case["name"], case["sha256"])
    measured = {name: run_worker("strict", raw) for name, raw in data.items()}
    for name, row in measured.items():
        wanted = {"original": [12, 10], "moving": [12, 29], "unchanged": [12, 10], "selected": [18, 10]}[name]
        require(
            row["d1_mm"] == wanted and row["row_count"] == (30 if name == "original" else 31)
            and row["lineage"].get("native_independent_stock_merge_tolerance_m") == (None if name == "original" else 1e-5),
            "the public SDK result lost an owned driver or observed tolerance",
        )
    omitted = run_worker("no-brep", data["moving"])
    cold = pinned(previous / "GeneratedTwoStockGraph01.SLDPRT", GENERATED)
    negatives = {name: run_worker(name, cold if name == "cold" else data["moving"]) for name in NEGATIVE}
    require(
        all(sha256((ROOT / name).read_bytes()).hexdigest() == digest for name, digest in source_sha256.items()),
        "the SDK implementation changed during the process comparison",
    )
    return {
        "schema": "kit.sw2026.disclosed-saved-two-stock-sdk-read.v1",
        "base_revision": check_output(("git", "rev-parse", "HEAD"), cwd=ROOT, text=True).strip(),
        "script_sha256": sha256(HERE.read_bytes()).hexdigest(),
        "implementation_sha256": source_sha256,
        "tolerance_receipt_sha256": TOLERANCE, "strict_reads": measured, "no_brep": omitted,
        "refusals": negatives, "guarded_processes": len(measured) + 1 + len(negatives),
        "held_out_cases": 0,
    }


if __name__ == "__main__":
    parser = ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--workspace", type=Path)
    mode.add_argument("--worker", choices=("strict", "no-brep", *NEGATIVE))
    args = parser.parse_args()
    result = worker(args.worker) if args.worker else prove(args.workspace)
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
