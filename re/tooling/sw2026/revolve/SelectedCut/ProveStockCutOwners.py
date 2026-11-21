from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from hashlib import sha256
from io import BytesIO
from math import isclose
from pathlib import Path
from subprocess import check_output, run
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
sys.path[:0] = [str(path) for path in (ROOT / "src", HERE.parent, HERE.parent.parent / "PrincipalWriter",
                                      HERE.parent.parent / "EndModes")]

from AuditRevEndOwners import guard_runtime
from convert.api.ApiContext import GetRegistry
from ProveTwoDirectionRevolves import warm
from convert.adapters.solidworks.Archive.Config.ReadConfigMut import ReadConfigMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileText
from convert.adapters.solidworks.Core.Preparation.Revolve.CanPrepRevolve import CanPrepRevolve
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockAtoms import ReadStockAtoms
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadParents import ReadParents
from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevCore import ReadRevCore
from StockCutFixture import DESIGNS, fixture
from StockCutGeometry import cut_measure
from StockCutOwners import build_owners
from StockCutPlan import require


BASE_REVISION = "4fc94b24a818303f45549f2b725bc92e98a867f3"
LOCK_REVISION = "642b20cc65d14262ecc1e78e478af5ab48ca59b0"
LOCK_SHA = "67c1aeca25817846925f18e5b6b7b9319bdba216835e685988961e0db8832f68"
LOCK_FILE = "re/solidworks/measurements/2026/RevolveCutHeldoutSourceLock01.json"
VERSION = 19000
INVALID_NEUTRAL = {
    "cross-selection": "selected stock reference differs",
    "cross-driver": "unlinked or unowned angle parameter",
    "cross-axis": "coaxial full stocks",
    "reverse-cut": "coaxial full stocks",
}
INVALID_LINKED = {
    "cross-consumed": "consumed and surviving atom states differ",
    "drop-primary": "two stock result identity differs",
}
WIRE_GATE = ("moCompSolidBody_c.{f100,f104,f108,ff0}",
             "moFaceRef_c.{f70,fe8,ordered chooser arrays}",
             "cold revolved-cut boundary and active cache policy")


def digest(data):
    return sha256(data).hexdigest()


def node_id(node, field="f08"):
    return node.FieldsValue[field]


def scope_row(rep):
    keeper = rep.FieldsValue["f10"]["f10"]
    data = keeper.FieldsValue["f10"]
    return [rep.ClassValue.NameValue, data["f00"], data["f08"], node_id(rep, "f38")]


def reference_report(owners):
    header = owners.headers[0]
    component = owners.selector.local_component
    require(component.FieldsValue["owner"] is owners.system.RootValue and component.FieldsValue["has_ext"] == 0,
            "historical stock owner is not the actual generated part")
    require(owners.selector.candidates is owners.geometry.stocks[owners.plan.selected_index],
            "selector candidates do not belong to the actual consumed stock")
    all_faces = (*owners.geometry.stocks[0], *owners.geometry.stocks[1], *owners.geometry.result)
    reps = tuple(rep for face in all_faces for rep in (face.own, *face.adjacent))
    refs = tuple(rep.FieldsValue["f10"]["f10"] for rep in reps)
    files = {ref.FieldsValue["f08"] for ref in refs}
    require(len(files) == 1 and header.FieldsValue["f38"] not in files and len(set(refs)) == len(refs) == len(set(reps)),
            "generated surfaces need distinct keepers and the same separate local file owner")
    external, = files
    self_file = header.FieldsValue["f38"]
    first, second = (value.FieldsValue["shared"] for value in (external, self_file))
    handles = ("h10", "h18")
    require(external.FieldsValue["refcfg"] == self_file.FieldsValue["refcfg"]
            and {key: value for key, value in first.items() if key not in handles}
            == {key: value for key, value in second.items() if key not in handles}
            and all(first[key] is not second[key] and ReadFileText(first[key]) == ReadFileText(second[key])
                    for key in handles), "generated keeper file has a foreign configuration or locator")
    members = tuple([scope_row(face.own), sorted(map(scope_row, face.adjacent))] for face in all_faces)
    return {"stock_surfaces": members[:4], "cut_end_surfaces": members[4:],
            "bounds": [node.FieldsValue for node in owners.geometry.bounds],
            "surface_representatives": len(reps), "local_file_is_distinct_from_header": True}


def read_core(owners):
    header_bytes = tuple(WriteHeadGraph(node, VERSION) for node in owners.headers[:2])
    config_bytes, config = WriteConfigMut(owners.system.RootValue, VERSION, owners.headers[0])
    context = {"model_compressed_stream": 1, "model_is_part": 1,
               "cmgr_f658": owners.system.ManagerValue.FieldsValue["f658"]}
    resolved_bytes, _ = WriteResolMut(owners.roots, None, VERSION, config.MapValue, context)

    header, top = tuple(ReadHeaderGraph(raw, VERSION) for raw in header_bytes)
    config_read = ReadConfigMut(config_bytes, VERSION, header)
    resolved = ReadResolvedMut(resolved_bytes, VERSION, config_read.MapValue, context)
    link = NativeLink(config_read, resolved, owners.plan.operations[0].ConfigName, "generated model probe")
    require(config_bytes == WriteConfigMut(config_read.RootValue, VERSION, header)[0]
            and resolved_bytes == WriteResolMut(resolved.RootsValue, resolved.ExtraFields, VERSION, config_read.MapValue, context)[0]
            and header_bytes == (WriteHeadGraph(header, VERSION), WriteHeadGraph(top, VERSION)),
            "generated graph replay differs")
    account = {"header2": header_bytes[1], "config_header": header_bytes[0], "config": config_bytes, "resolved": resolved_bytes}
    return link, {key: {"bytes": len(raw), "sha256": digest(raw)} for key, raw in account.items()}


def read_ops(owners, link):
    from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import DatumTime

    ordered = link.ResolvedValue.RootsValue[-6:]
    nodes, profiles = ordered[1::2], ordered[::2]
    features = IndexFeatures(link)
    require([node.ClassValue.NameValue for node in nodes] == ["moRevolution_c", "moRevolution_c", "moRevCut_c"]
            and tuple(ReadParents(node) for node in nodes) == tuple((profile,) for profile in profiles),
            "concrete operation/profile ownership differs on linked readback")
    operations = [ReadRevCore(link, node, profile, features, code)
                  for node, profile, code in zip(nodes, profiles, (1, 0, 1), strict=True)]
    expected = owners.plan.operations
    require(len({op.AngleValue.HandleValue for op in operations}) == len({op.AxisValue.HandleValue for op in operations}) == 3
            and len({op.AngleValue.ParameterValue for op in operations}) == 3
            and len({op.AngleValue.DimensionValue for op in operations}) == 3,
            "axis handle or angle resource reused another operation's owner")
    for op, plan in zip(operations, expected, strict=True):
        require(op.AngleValue.NameValue == "D1" and op.AngleValue.RadiansValue == plan.AngleValue
                and op.EndValue.ModeValue == "one_sided" and op.EndValue.AgainstValue is None
                and not op.IsReverse and op.ProfileGraph.EqualValue is None
                and DatumTime(link.ConfigValue.HeaderValue, node_id(op.NodeValue)) == owners.settings.HeaderValue.CreatedAt,
                "linked cut operation changed active driver, end, or creation owner")
    return nodes, [{"profile_id": node_id(op.ProfileValue), "feature_id": node_id(op.NodeValue),
                    "angle_rad": op.AngleValue.RadiansValue, "axis_mark": op.ProfileGraph.AxisValue.PermanentId,
                    "mode": op.EndValue.ModeValue, "dimension_id": node_id(op.AngleValue.DimensionValue, "f50")}
                   for op in operations]


def check_linked(owners, link, fault):
    nodes, measurements = read_ops(owners, link)
    selected = owners.plan.selected_index
    if fault == "cross-consumed":
        nodes[2].FieldsValue["f530"]["items"][0]["o"] = nodes[1 - selected].FieldsValue["f528"]["items"][0]["o"]
    elif fault == "drop-primary":
        nodes[2].FieldsValue["f498"][0]["v"] = 0
    lineage = ReadStockAtoms(link, *nodes)
    require(lineage.SelectedIndex == selected, "linked scope changed its actual selected stock")
    atom_order = (lineage.ConsumedAtom, lineage.UntouchedAtom, lineage.ResultAtom)
    report = {name: node_id(atom, "f140") for name, atom in zip(("consumed", "untouched", "result"), atom_order, strict=True)}
    return report, measurements


def worker(request):
    design = DESIGNS[request["design"]]
    fault = request.get("fault")
    warm()
    writer = GetRegistry().GetWriter("solidworks.sldprt")
    blocked = guard_runtime()
    try:
        document = fixture(design, fault)
        locator = f'C:\\KitScope\\{design["name"]}.SLDPRT'
        require(not CanPrepRevolve(document, locator, design["epoch"]), "ordinary revolve unexpectedly admitted the cut")
        owners = build_owners(document, locator, design["epoch"])
        link, streams = read_core(owners)
        atoms, drivers = check_linked(owners, link, fault)
        measure = [asdict(value) for value in cut_measure(owners.plan)]
        require(all(value["volume_m3"] > 0 and value["area_m2"] > 0 for value in measure)
                and [value["face_count"] for value in measure] == [4, 9], "unexpected analytic body partition")
        require(not fault, f"unsupported model was admitted: {fault}")
        require(not writer.supports(document, locator), "normal registry unexpectedly admitted the cut")
        destination = BytesIO()
        try:
            writer.write(document, destination)
        except (TypeError, ValueError) as error:
            refusal = str(error)
        else:
            raise ValueError("normal SDK write unexpectedly admitted the cut")
        require(not destination.getvalue(), "denied ordinary write emitted bytes")
        result = {"selected": design["selected"], "reached_wall": owners.plan.reached_wall,
                  "cut_wall": owners.plan.result_wall, "atoms": atoms, "drivers": drivers, "stream_probe": streams,
                  "config_counter": link.ConfigValue.MapValue.CounterValue,
                  "resolved_counter": link.ResolvedValue.MapValue.CounterValue, "bodies": measure,
                  "support_axis": owners.plan.operations[0].AxisValue, "references": reference_report(owners),
                  "direct_writer_refused": refusal, "denied_destination_bytes": len(destination.getvalue())}
    except ValueError as error:
        expected = (INVALID_NEUTRAL | INVALID_LINKED).get(fault)
        require(expected is not None and expected in str(error), str(error))
        result = {"refused": str(error)}
    require(not blocked and not any(name in ("Swapp", "pythoncom", "pywintypes") or name.startswith("win32com")
                                   for name in sys.modules), "guarded operation used host files or a CAD runtime")
    return result | {"runtime_file_reads": len(blocked), "ordinary_preparation_refused": True}


def execute(request):
    child = run((sys.executable, "-I", "-B", str(HERE), "--worker"), input=json.dumps(request).encode(),
                capture_output=True, timeout=60)
    require(child.returncode == 0 and not child.stderr, child.stderr.decode())
    return json.loads(child.stdout)


def main(output):
    require(output.is_absolute() and output.suffix == ".json",
            "receipt requires an exact JSON destination")
    tree = check_output(("git", "rev-parse", BASE_REVISION + ":src"), cwd=ROOT, text=True).strip()
    for ancestor in (LOCK_REVISION, BASE_REVISION):
        status = run(("git", "merge-base", "--is-ancestor", ancestor, "HEAD"), cwd=ROOT, check=False)
        require(status.returncode == 0, "actual pre-writer lock and reader intake must precede the constructor")
    require(digest((ROOT / LOCK_FILE).read_bytes()) == LOCK_SHA, "pre-writer public custody metadata differs")
    requests = [{"design": index} for index in range(len(DESIGNS))]
    requests.extend({"design": index % len(DESIGNS), "fault": fault} for index, fault in
                    enumerate((*INVALID_NEUTRAL, *INVALID_LINKED)))
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(execute, requests))
    require(len({entry["stream_probe"]["resolved"]["sha256"] for entry in results[:2]}) == len(DESIGNS)
            and not isclose(results[0]["bodies"][1]["volume_m3"], results[1]["bodies"][1]["volume_m3"]),
            "two authored models did not vary actual graph and geometry")
    files = (HERE, *(HERE.with_name(name) for name in
                     ("StockCutPlan.py", "StockCutOwners.py", "StockCutGeometry.py", "StockCutFixture.py")),
             *(ROOT / "src/convert/adapters/solidworks/Archive/Construction/Revolves/Feature" / name
               for name in ("MakeRevNodeMut.py", "MakeRevFeatMut.py")),
             ROOT / "src/convert/adapters/solidworks/Archive/Construction/Dimensions/RequireDisplay.py")
    changed = set(check_output(("git", "diff", "--name-only", BASE_REVISION, "--", "src"),
                               cwd=ROOT, text=True).splitlines())
    require(changed == {str(path.relative_to(ROOT)) for path in files if path.is_relative_to(ROOT / "src")},
            "source changes exceed the exact three typed factory paths")
    receipt = {"schema": "kit.sw2026.selected-revolve-cold-owners.v1", "source_parent": BASE_REVISION, "source_parent_tree": tree,
               "tool_and_candidate_digests": {str(path.relative_to(ROOT)): digest(path.read_bytes()) for path in files},
               "prewriter_lock_metadata_sha256": LOCK_SHA, "prewriter_lock_revision": LOCK_REVISION,
               "designs": DESIGNS, "processes": [request | {"result": evidence}
                                               for request, evidence in zip(requests, results, strict=True)],
               "wire_gate": WIRE_GATE, "native_artifacts_written": 0, "native_processes": 0, "heldout_inputs_read": 0}
    raw = (json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    with output.open("xb") as stream:
        stream.write(raw)
    print(digest(raw))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(json.load(sys.stdin)), allow_nan=False))
    else:
        main(args.output)
