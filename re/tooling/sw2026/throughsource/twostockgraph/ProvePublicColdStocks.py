from argparse import ArgumentParser
from hashlib import sha256
from importlib import import_module
from io import BytesIO
from math import acos, isclose, pi, sqrt
from pathlib import Path
from subprocess import check_output, run
import codecs
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
SHAPE = HERE.parent.parent / "twostockshape"
BASE = "6d4fa7929ad7426ae088b770c7794d794ab3e57c"
ORDINARY = "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6"
SAVED_CONTROL = "748cdbec3fe61d6801f3d606e64fe42ecba95e9a647897be3fe3790570a889f3"
CACHE_STOP = "SLDPRT contains no readable Parasolid payload"
FAULTS = {
    "crossed-atom": "cut selection wrapper differs from the consumed boss atom",
    "crossed-datum": "cut and selected stock do not share their exact signed datum",
    "realized-result": "pre-rebuild solid has a result, consumed atom or chooser owner",
    "present-cache": None,
}


def bore():
    from BuildTwoStockGraph import build_owner_graph
    from LinkTwoStockGraph import link_graph
    from ProofModels import AUTHORED
    from ProveTwoStockGraph import make_document

    values = {**AUTHORED["disclosed-initial"], "circle": (21, -8, 2)}
    return link_graph(
        build_owner_graph(make_document(values, "bore"), 1765500071)
    ).payload


def fault_bytes(raw, fault):
    from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
    from convert.adapters.solidworks.Container.Container import (
        BuildSldprt,
        SldprtArchive,
    )
    from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ReadColdOwners import (
        ReadColdOwners,
    )
    from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import (
        ReadNativeLink,
    )
    from ProveRebuiltColdStocks import require

    archive = SldprtArchive.from_bytes(raw)
    streams = dict(archive.streams)
    if fault == "present-cache":
        streams["Contents/Config-0-Partition"] = b""
    else:
        link = ReadNativeLink(archive, 0)
        owners = ReadColdOwners(link)
        wrapper = owners.WrapperValue.FieldsValue
        other = owners.StockValues[1 - owners.SelectedIndex].NodeValue
        other_id = owners.StockAtoms[1 - owners.SelectedIndex].FieldsValue["f140"]
        if fault == "crossed-atom":
            wrapper["f18"] = other_id
        elif fault == "crossed-datum":
            wrapper.update(
                f108=NativeNodeId(other),
                f18=other_id,
                f1c=other_id,
                f110=[{"v": other_id}],
            )
        elif fault == "realized-result":
            cut = owners.CutValue.NodeValue.FieldsValue
            cut.update(has_f528=1, f528=other.FieldsValue["f528"])
        try:
            ReadColdOwners(link)
        except ValueError as error:
            require(str(error) == FAULTS[fault], str(error))
        else:
            raise ValueError("malformed linked cold ownership unexpectedly qualified")
        streams[link.StreamName], _ = WriteResolMut(
            link.ResolvedValue.RootsValue,
            link.ResolvedValue.ExtraFields,
            19000,
            link.ConfigValue.MapValue,
            link.ResolvedValue.ContextValue,
        )
    return BuildSldprt(streams, FormatVersion=4)


def inspect_document(doc):
    from ProveRebuiltColdStocks import require

    require(not doc.validate(), "public projection does not validate")
    report = doc.metadata["solidworks.typed_resolved_semantics"]
    return {
        "semantic_sha256": sha256(doc.to_json().encode()).hexdigest(),
        "feature_ids": [step.id for step in doc.feature_timeline],
        "typed_status": report["status"],
        "body_binding": report.get("cut_body_dependency"),
        "tree_status": report.get("native_tree", {}).get("status"),
        "diagnostics": [(value.code, value.message) for value in doc.diagnostics],
        "payload_count": len(doc.brep_payloads),
        "brep_ids": (
            [body.design_body_id for body in doc.brep.bodies] if doc.brep else []
        ),
        "bodies": {
            body.name: {
                "id": body.id,
                "final_feature_id": body.final_feature_id,
                "solid_count": body.topology.solid_count,
                "faces": body.topology.face_count,
                "volume_mm3": body.topology.volume,
                "area_mm2": body.topology.surface_area,
                "centre_mm": body.attributes.get("solidworks.body_centroid_mm"),
            }
            for body in doc.bodies
        },
    }


def inspect_cold(doc, report):
    from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
    from interchange.geometry.Models.Selection import SelectPathElem
    from ProveRebuiltColdStocks import require

    evidence = doc.metadata["solidworks.typed_resolved_semantics"]
    binding = report["body_binding"]
    tree = evidence["native_tree"]
    require(
        "consumed_atom_id" not in binding
        and "result_atom_id" not in binding
        and binding["binding"] == "cold_two_stock_explicit_wrapper"
        and tree["status"] == "ordinary_cold_selected_two_stock_profile"
        and len(tree["retained_public_ids"]) == len(report["feature_ids"]) == 23
        and not tree["configuration_helpers"]
        and not tree["member_ids"]
        and len(doc.configurations) == 1
        and doc.configurations[0].name == "Default"
        and doc.brep is not None
        and len(doc.bodies) == len(doc.brep.bodies) == 2
        and report["brep_ids"] == [body.id for body in doc.bodies]
        and not doc.brep_payloads
        and any(diag.code == "sldprt.brep_reconstructed" for diag in doc.diagnostics),
        "public cold path did not retain its two independent derived owners",
    )
    by_id = {step.id: step for step in doc.feature_timeline}
    stock, untouched, cut = (
        by_id[f"sldprt:feature:{binding[key]}"]
        for key in (
            "producer_feature_id",
            "untouched_producer_feature_id",
            "consumer_feature_id",
        )
    )
    (selection,) = (
        value for value in doc.selections if value.id == cut.id + ":stock-body"
    )
    require(
        stock.operation == untouched.operation == "create"
        and cut.operation == "cut"
        and len(stock.parameter_ids) == len(untouched.parameter_ids) == 1
        and not cut.parameter_ids
        and selection.path == (SelectPathElem("feature", stock.id, "body"),)
        and cut.selection_ids == (selection.id,)
        and cut.input_feature_ids[0] == stock.id
        and untouched.id not in cut.input_feature_ids
        and doc.bodies[0].final_feature_id == untouched.id
        and doc.bodies[1].final_feature_id == cut.id
        and isinstance(cut.definition, ExtrudeFeature)
        and cut.definition.end_condition == ExtrudeEnd.KThroughAll
        and not cut.definition.reversed
        and cut.definition.direction is not None
        and cut.attributes.get("direction_code") == 1,
        "public extrusion order, dimensions or actual selected stock differ",
    )
    params = {param.id: param for param in doc.parameters}
    depths = [params[value.parameter_ids[0]] for value in (stock, untouched)]
    require(
        all(
            param.name == "D1" and param.owner_id == owner.id
            for param, owner in zip(depths, (stock, untouched), strict=True)
        )
        and depths[0].id != depths[1].id,
        "public driving parameter roles differ",
    )
    direction = cut.definition.direction
    report.update(
        selected_id=stock.id,
        cut_direction=[direction.x, direction.y, direction.z],
        picked=[
            (value.entity_kind, value.entity_id, value.subelement)
            for value in selection.path
        ],
        depths={param.owner_id: param.value.value for param in depths},
    )


def read_public(raw, mode):
    from convert import open_document
    from convert.adapters.base.ReadOptions import ReadOptions
    from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
    from ProveRebuiltColdStocks import identity

    try:
        if mode == "raw":
            doc = SldprtAdapter().read(BytesIO(raw), ReadOptions(extract_raw_brep=True))
        else:
            doc = open_document(
                raw,
                source_format="solidworks.sldprt",
                configuration="Default" if mode == "edited" else None,
                include_brep=mode != "no-brep",
                include_tessellation=False,
                strict=True,
            )
    except ValueError as error:
        return {"archive": identity(raw), "refusal": str(error)}
    report = inspect_document(doc)
    if mode in ("initial", "edited", "second", "bore"):
        inspect_cold(doc, report)
    return {"archive": identity(raw), **report}


def worker(mode, sdk):
    sys.path[:0] = [str(sdk), str(HERE.parent), str(SHAPE)]
    deps = [
        "convert",
        "convert.adapters.solidworks.Core.Adapter",
        "interchange.brep.Validation.BrepValidate",
        "interchange.document.Behavior.DocumentIo",
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Validation.DocumentValidate",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
    ]
    if mode in ("edited", "second", "bore", *FAULTS):
        deps += [
            "BuildTwoStockGraph",
            "LinkTwoStockGraph",
            "ProofModels",
            "ProveTwoStockGraph",
        ]
    for name in deps:
        import_module(name)
    for encoding in (
        "ascii",
        "latin-1",
        "utf-8",
        "utf-8-sig",
        "utf-16-le",
        "utf-16-be",
    ):
        codecs.lookup(encoding)
    from ProveRebuiltColdStocks import independent_input, require

    attempts = []

    def audit(event, _):
        if event in {
            "open",
            "os.listdir",
            "os.scandir",
            "os.system",
            "os.exec",
            "os.fork",
            "os.posix_spawn",
            "os.startfile",
        } or event.startswith(("subprocess.", "socket.", "ctypes.", "winreg.")):
            attempts.append(event)
            raise PermissionError("public cold stock worker attempted " + event)

    sys.addaudithook(audit)
    raw = sys.stdin.buffer.read()
    if mode in ("edited", "second", "bore", *FAULTS):
        require(not raw, "fresh archive did not receive only the independent model")
        raw = (
            bore()
            if mode == "bore"
            else independent_input(mode if mode == "second" else "edited")
        )
        if mode in FAULTS:
            raw = fault_bytes(raw, mode)
    result = read_public(raw, mode)
    require(not attempts, "public cold stock worker attempted external access")
    return {**result, "runtime_access_attempts": len(attempts)}


def run_worker(mode, payload, sdk):
    from ProveRebuiltColdStocks import require

    output = run(
        (sys.executable, "-I", "-B", str(HERE), "--worker", mode, "--sdk", str(sdk)),
        input=payload,
        capture_output=True,
        timeout=90,
    )
    require(output.returncode == 0, f"{mode}: {output.stderr.decode()}")
    return json.loads(output.stdout)


def verify(results):
    from ProveRebuiltColdStocks import compare_measures, pinned, require, NATIVE_RECEIPT

    path = ROOT / "re/solidworks/measurements/2026/TwoStockColdNative01.json"
    snapshots = json.loads(pinned(path, NATIVE_RECEIPT))["snapshots"]
    names = (("MovingStock", "MovingStock"), ("ThroughFeature", "SteadyStock"))
    first, edit, right, hole = (
        results[name] for name in ("initial", "edited", "second", "bore")
    )
    compare_measures(first, snapshots["initial"], names)
    compare_measures(edit, snapshots["fresh_reopen"], names)
    require(
        first["bodies"]["ThroughFeature"] == edit["bodies"]["ThroughFeature"]
        and first["cut_direction"]
        == edit["cut_direction"]
        == hole["cut_direction"]
        == [0, 0, 1]
        and right["cut_direction"] == [1, 0, 0]
        and first["depths"] == {"sldprt:feature:19": 12, "sldprt:feature:22": 10}
        and edit["depths"] == {"sldprt:feature:19": 12, "sldprt:feature:22": 29}
        and right["body_binding"]["selected_stock_atom_id"]
        != first["body_binding"]["selected_stock_atom_id"]
        and hole["bodies"]["ThroughFeature"]["faces"] == 7
        and isclose(
            hole["bodies"]["ThroughFeature"]["volume_mm3"],
            12 * (18 * 8 - pi * 2**2),
            rel_tol=1e-12,
        ),
        "authored depth edit, second selection or enclosed tool disagrees",
    )
    segment = 7**2 * acos(5 / 7) - 5 * sqrt(7**2 - 5**2)
    require(
        set(right["bodies"]) == {"AlphaSolid", "RightScopeCut"}
        and isclose(
            right["bodies"]["RightScopeCut"]["volume_mm3"],
            (11 * 14 - segment) * 9.5,
            rel_tol=1e-12,
        ),
        "independent Right body does not match analytic volume",
    )


def prove(packet, baseline):
    sys.path.insert(0, str(HERE.parent))
    from ProveRebuiltColdStocks import (
        GENERATED,
        NATIVE_SAVED,
        NATIVE_RECEIPT,
        pinned,
        require,
    )

    head = check_output(("git", "rev-parse", "HEAD"), cwd=ROOT, text=True).strip()
    require(head == BASE, "use the exact cold stock read baseline")
    require(
        packet.name == "GeneratedTwoStockGraph01" and not packet.is_symlink(),
        "use only the disclosed packet",
    )
    adapter = "convert/adapters/solidworks/Core/Adapter.py"
    original = check_output(("git", "show", f"{BASE}:src/{adapter}"), cwd=ROOT)
    require(
        (baseline / adapter).read_bytes() == original, "baseline SDK source differs"
    )
    sdk = ROOT / "src"
    results = {
        mode: run_worker(mode, b"", sdk)
        for mode in ("edited", "second", "bore", *FAULTS)
    }
    for fault in FAULTS:
        require(
            results[fault]["refusal"] == CACHE_STOP,
            "unsupported archive bypassed strict cache refusal",
        )
    initial_path = packet / "GeneratedTwoStockGraph01.SLDPRT"
    initial = pinned(initial_path, GENERATED)
    results["initial"] = run_worker("initial", initial, sdk)
    verify(results)
    old = run_worker("original", initial, baseline)
    require(old["refusal"] == CACHE_STOP, "prior strict result was different")
    saved_path = packet / "NativeAfterEdit.SLDPRT"
    derivative = pinned(saved_path, NATIVE_SAVED)
    control_path = (
        packet.parent
        / "ThroughMultiStock03"
        / "DisclosedNative"
        / "ThroughMultiStock.SLDPRT"
    )
    saved = pinned(control_path, SAVED_CONTROL)
    ordinary = pinned(
        ROOT / "re/solidworks/v2026/corpus/ladder/L1_boss.SLDPRT", ORDINARY
    )
    unaffected = {
        "no-brep": initial,
        "raw": initial,
        "saved": saved,
        "ordinary": ordinary,
        "saved-derivative": derivative,
    }
    for mode, payload in unaffected.items():
        current = run_worker(mode, payload, sdk)
        prior = run_worker(mode, payload, baseline)
        require(prior == current, f"existing {mode} path differs")
        if mode == "saved":
            require(
                current["body_binding"]["binding"] == "saved_two_stock_atom_alias",
                "saved control did not reach its original two-stock cache route",
            )
        results[mode] = current
    require(
        results["raw"]["refusal"] == CACHE_STOP
        and not results["no-brep"]["brep_ids"]
        and not results["no-brep"]["payload_count"]
        and results["ordinary"]["payload_count"] > 0,
        "raw payload request, no-Brep projection or ordinary saved read changed",
    )
    require(
        pinned(initial_path, GENERATED) == initial
        and pinned(saved_path, NATIVE_SAVED) == derivative
        and pinned(control_path, SAVED_CONTROL) == saved,
        "disclosed comparison changed",
    )
    changes = check_output(
        ("git", "diff", "--name-only", BASE, "--", "src"), cwd=ROOT, text=True
    ).splitlines()
    cold = sdk / "convert/adapters/solidworks/Core/TypedResolved/Cuts/MultiStock"
    fresh = (
        *sorted((cold / "Cold").glob("*.py")),
        *(
            cold / name
            for name in ("BindStockModel.py", "IsStockModel.py", "IsStockConfig.py")
        ),
        sdk
        / "convert/adapters/solidworks/Core/TypedResolved/Presentation/CheckColdRows.py",
        sdk
        / "convert/adapters/solidworks/Core/TypedResolved/Geometry/ReadPartShape.py",
    )
    tools = (HERE, *(ROOT / name for name in changes), *fresh)
    return {
        "schema": "kit.sw2026.public-cold-stock-reader.v1",
        "baseline": head,
        "native_receipt_sha256": NATIVE_RECEIPT,
        "source_sha256": {
            str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest()
            for path in tools
        },
        "guarded_processes": len(results) + len(unaffected) + 1,
        "runtime_access_attempts": sum(
            value["runtime_access_attempts"] for value in results.values()
        ),
        "baseline_refusal": old,
        "unchanged_against_baseline": tuple(unaffected),
        "native_launches": 0,
        "held_out_cases": 0,
        "phases": results,
    }


if __name__ == "__main__":
    parser = ArgumentParser()
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--packet", type=Path)
    actions.add_argument("--worker")
    parser.add_argument("--sdk", type=Path, required=True)
    args = parser.parse_args()
    result = (
        worker(args.worker, args.sdk) if args.worker else prove(args.packet, args.sdk)
    )
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
