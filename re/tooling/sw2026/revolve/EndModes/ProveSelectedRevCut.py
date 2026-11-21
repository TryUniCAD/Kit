from argparse import ArgumentParser
from copy import copy
from hashlib import sha256
from math import isclose, radians, tau
import json
from pathlib import Path
from subprocess import check_output, run
import sys


HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
sys.path[:0] = [str(HERE.parent), str(ROOT / "src"), str(HERE.parent.parent / "PrincipalReader")]
BASE = "4de7606b44e84da5b84f10847d03f42d710ad29f"
LOCK = "9a1fab4e8d62532dbcc2a49b48e0228f47e134c1bbc29dd5c81f04aa90bb6075"
BUILD = "34.5.2.0604"
CASES = ("RevCutInner", "RevCutOuter")
FAULTS = {"wrong-result": "wrapper does not alias", "wrong-stock-atom": "consumed and surviving atom states",
          "crossed-axis": "axis is outside", "wrong-merge": "direction type or converted sketch",
          "wrong-clock": "creation owner", "detached-face": "does not alias its archive map",
          "wrong-mirror": "mirrored surface ownership", "ambiguous-selector": "one actual array member"}


def digest(data):
    return sha256(data).hexdigest()


def need(value, message):
    if not value:
        raise ValueError(message)


def checked(path, pin):
    raw = path.read_bytes()
    need(not path.is_symlink() and digest(raw) == pin, "the disclosed observation changed: " + path.name)
    return raw


def bad_graph(link, cut_id, slots, fault):
    from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures

    nodes = IndexFeatures(link)
    first, second, cut = (nodes[number] for number in (*slots, cut_id))
    fields = cut.FieldsValue
    wrapper = fields["f548"]["items"][0]["o"].FieldsValue
    face = wrapper["ff0"]
    if fault == "wrong-result":
        wrapper["f104"] = wrapper["f18"]
    elif fault == "wrong-stock-atom":
        fields["f530"] = second.FieldsValue["f528"]
    elif fault == "crossed-axis":
        fields["f830"] = first.FieldsValue["f830"]
    elif fault == "wrong-merge":
        second.FieldsValue["f870"] = 1
    elif fault == "wrong-clock":
        ref = face.FieldsValue["f10"][0]["f08"].FieldsValue["f10"]["f10"].FieldsValue["f10"]
        ref["f08"] += 1
    elif fault == "detached-face":
        wrapper["ff0"] = copy(face)
    elif fault == "wrong-mirror":
        choose = fields["f4c0"]["f48"]["items"][0]["o"].FieldsValue["f08"]["items"]
        choose.reverse()
    elif fault == "ambiguous-selector":
        fields["f548"]["n"] = 2
        fields["f548"]["items"].append(fields["f548"]["items"][0])
    else:
        raise ValueError("unknown fault")


def case_evidence(doc, proof, cache, row):
    from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
    from interchange.Features.FeatureAngleRev import AngularRevolve

    info = doc.metadata["solidworks.typed_revolve_cut"]
    stock = proof.SelectedValue
    untouched = proof.UntouchedValue
    observed = row["reopened"]
    scope = observed["definition"]["scope"]
    need(scope["feature_scope"] and not scope["auto_select"] and scope["count"] == 1 and scope["array_present"]
         and scope["stock_owners"] == [ReadNativeName(stock.NodeValue)], "the actual native selection differs")
    ops = [step for step in doc.feature_timeline if isinstance(step.definition, AngularRevolve)]
    graph_ops = (*proof.StockValues, proof.CutValue)
    need([step.id for step in ops] == [f"sldprt:feature:{NativeNodeId(owner.NodeValue)}" for owner in graph_ops]
         and [step.operation.value for step in ops] == ["create", "create", "cut"], "actual production timeline")
    chosen = ops[proof.AtomsValue.SelectedIndex]
    cut = ops[-1]
    need(cut.input_feature_ids == (f"sldprt:feature:{NativeNodeId(proof.CutValue.ProfileValue)}", chosen.id),
         "portable cut consumption must agree with its selected earlier body")
    selections = {value.id: value for value in doc.selections}
    assert selections[cut.selection_ids[-1]].path[0].entity_id == chosen.id
    assert selections[cut.selection_ids[-1]].path[0].subelement == "body"
    params = {value.id: value for value in doc.parameters}
    sketches = {value.id: value for value in doc.sketches}
    angles = []
    for step, owner, expected in zip(ops, graph_ops, (tau, tau, radians(row["job"]["case"]["angle_deg"])), strict=True):
        driver = params[step.definition.AlongParameterId]
        sketch = sketches[step.sketch_id]
        axis = selections[step.definition.AxisSelectionId]
        need(driver.owner_id == step.id and driver.name == "D1" and driver.value.unit == "rad" and driver.role.value == "driving"
             and isclose(driver.value.value, expected, abs_tol=1e-13, rel_tol=0)
             and step.definition.SideMode == "one_sided" and step.definition.AgainstParameterId is None
             and driver.attributes["typed_archive_owner"]["slot"] == "f8d8.f18"
             and len(sketch.entities) == 5 and len(sketch.constraints) == 4
             and axis.path[0].entity_id == sketch.id and any(
                 value.id == axis.path[1].entity_id and value.construction for value in sketch.entities), "owned end, driver and axis")
        angles.append({"radians": driver.value.value, "owner": driver.attributes["typed_archive_owner"],
                       "axis_mark": owner.ProfileGraph.AxisValue.PermanentId, "selection_mark": owner.AxisValue.MarkValue,
                       "axis_endpoints_mm": axis.attributes["native_ordered_endpoints_mm"]})
    need(len(doc.bodies) == len(doc.brep.bodies) == 2 and doc.brep == cache.BrepValue and not doc.brep.validate(
        frozenset(body.id for body in doc.bodies)), "actual two-body geometry membership")
    bodies = []
    native_names = {value["name"]: value for value in observed["measured"].values()}
    for actual, mapped, owner in zip(doc.bodies, doc.brep.bodies, cache.BodyValues, strict=True):
        measured = native_names[actual.name]
        need(actual.id == mapped.design_body_id == owner.DesignId and actual.topology.face_count == measured["faces"],
             "typed physical face count differs from the native body")
        bodies.append({"atom_id": owner.AtomId, "producer_id": NativeNodeId(owner.ProducerValue),
                       "body_index": owner.KernelValue.IndexValue, "design_id": actual.id, "faces": measured["faces"],
                       "native_volume_m3": measured["volume_m3"], "native_area_m2": measured["area_m2"],
                       "native_centroid_m": measured["com_m"]})
    need([value["faces"] for value in bodies] == [4, 9] and info["selected_producer_id"] == NativeNodeId(stock.NodeValue)
         and bodies[0]["producer_id"] == NativeNodeId(untouched.NodeValue) and info["public_writer_qualified"] is False,
         "portable source read exceeded its actual body or writer boundary")
    return {"owners": info, "drivers": angles, "bodies": bodies, "scope": scope}


def worker(payload):
    from AuditPrincipalReader import make_guard
    from AuditRevEndOwners import audit_streams
    from ProveTwoDirectionRevolves import warm
    from convert import open_document
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.ReadRevCache import ReadRevCache
    from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.ReadSelRevCut import ReadSelRevCut

    raw = checked(Path(payload["path"]), payload["sha"])
    warm()
    state, audit = make_guard(ROOT / "src")
    state["enabled"] = True
    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    top = ReadHeaderGraph(archive.require("Header2"), 19000)
    lineage = ReadSelRevCut(link, top)
    if fault := payload.get("fault"):
        bad_graph(link, NativeNodeId(lineage.CutValue.NodeValue), tuple(NativeNodeId(row.NodeValue) for row in lineage.StockValues), fault)
        try:
            ReadSelRevCut(link, top)
        except ValueError as error:
            need(FAULTS[fault] in str(error), "wrong owner refusal: " + str(error))
            result = {"refused": str(error)}
        else:
            raise ValueError("changed owner did not refuse: " + fault)
    else:
        cache = ReadRevCache(archive, link, lineage)
        doc = open_document(raw, source_format="solidworks.sldprt", strict=True)
        history = open_document(raw, source_format="solidworks.sldprt", strict=True, include_brep=False, include_tessellation=False)
        need("solidworks.typed_revolve_cut" not in history.metadata and history.brep is None and not history.brep_payloads,
             "history-only options exceeded the proved saved geometry scope")
        replay = audit_streams(archive, link)
        result = case_evidence(doc, lineage, cache, payload["observed"]) | {"exact_streams": replay, "history_only_legacy": True}
    state["enabled"] = False
    need(not audit["unexpected_attempts"] and not any(name in ("Swapp", "pythoncom", "pywintypes") or name.startswith("win32com")
             for name in sys.modules), "strict reader accessed external data or a CAD runtime")
    return result | {"sha256": payload["sha"], "unexpected_runtime_reads": 0, "rule_file_reads": audit["grammar_reads"]}


def dispatch(path, sha, **kwargs):
    data = {"path": str(path), "sha": sha, **kwargs}
    child = run((sys.executable, "-I", "-B", str(HERE), "--worker"), input=json.dumps(data).encode(), capture_output=True, timeout=120)
    need(child.returncode == 0 and not child.stderr, child.stderr.decode())
    return json.loads(child.stdout)


def prove(folder):
    need(folder.parts[-2:] == ("RevolveCutDiscovery03", "Capture"), "use only the disclosed cut capture")
    lock = json.loads(checked(folder / "SourceLock.json", LOCK))
    need(lock["oracle_build"] == BUILD and not lock["passed"] and lock["inputs_unchanged"] and lock["idle_after"] and
         lock["writer_output_count"] == 0 and lock["distinct_processes"] == 9, "mixed native run provenance")
    cases, ids = {}, []
    for control in ("control-before", "control-after"):
        envelope = lock[control]
        phase = json.loads(checked(folder / (control + ".json"), envelope["sha256"]))
        need(envelope["passed"] and phase["opened"] and phase["open_errors"] == phase["open_warnings"] == 0
             and phase["rebuilt"] and not phase["dialogs"], "both independent exact controls required")
        ids.append(phase["oracle_identity"]["process_creation_filetime"])
    for source in lock["sources"]:
        name = source["case"]
        need(name in (*CASES, "RevCutAll"), "unexpected native input")
        phases = {}
        for info in source["phases"]:
            role = info["phase"]
            path = folder / name / ((name + "-edited" if role == "edited-reopen" else name) + f".{role}.json")
            phase = json.loads(checked(path, info["sha256"]))
            need(phase["passed"] is info["passed"] and phase["oracle_identity"]["sha256"] == lock["oracle_sha256"],
                 "native phase detached from the exact oracle")
            ids.append(phase["oracle_identity"]["process_creation_filetime"])
            phases[role] = phase
        if name == "RevCutAll":
            row = phases["author"]
            need(not source["passed"] and source["native_sha256"] is None and row["last_scope_observation"]["count"] == 2,
                 "the unrestricted trial must retain the reported refusal")
            cases[name] = {"saved_source_exists": False, "first_failure": row["first_failure"]["error"],
                           "actual_native_scope": row["last_scope_observation"]}
            continue
        initial = phases["reopen"]
        edited = phases["edited-reopen"]
        saved = initial["edited_derivative"]
        need(len(phases) == 3 and all(x["passed"] for x in phases.values()) and initial["edit"]["passed"]
             and saved["save_status"] == [True, 0, 0], "selected source needs all native lifecycle phases")
        original_path = folder / name / (name + ".SLDPRT")
        edited_path = folder / name / (name + "-edited.SLDPRT")
        cases[name] = {"original": dispatch(original_path, source["native_sha256"], observed=initial),
                       "edited": dispatch(edited_path, saved["sha256"], observed=edited)}
    need(len(set(ids)) == len(ids) == 9 and all(ids[0] < value < ids[1] for value in ids[2:]), "native phases outside brackets")
    source = lock["sources"][0]
    name = source["case"]
    original = folder / name / (name + ".SLDPRT")
    refused = {fault: dispatch(original, source["native_sha256"], fault=fault) for fault in FAULTS}
    paths = check_output(("git", "diff", "--name-only", BASE, "--", "src"), cwd=ROOT).decode().splitlines()
    paths += check_output(("git", "ls-files", "--others", "--exclude-standard", "--", "src"), cwd=ROOT).decode().splitlines()
    return {"schema": "kit.sw2026.selected-revolve-cut-read.v1", "source_lock_sha256": LOCK, "base": BASE,
            "source_files": {name: digest((ROOT / name).read_bytes()) for name in sorted(set(paths))},
            "case_results": cases, "guarded_processes": 4 + len(refused), "refused": refused,
            "native_phases_rechecked": 9, "new_native_phases": 0, "new_heldout_credit": 0, "public_writer": False}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--capture", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(json.load(sys.stdin)), sort_keys=True, allow_nan=False))
    else:
        result = prove(args.capture.resolve(strict=True))
        with args.output.open("x") as target:
            json.dump(result, target, sort_keys=True, indent=2, allow_nan=False)
            target.write("\n")
