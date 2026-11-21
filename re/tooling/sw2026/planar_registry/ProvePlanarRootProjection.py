from argparse import ArgumentParser
from codecs import lookup
from dataclasses import asdict, replace
from hashlib import sha256
from importlib import import_module
import json
import os
from pathlib import Path
from subprocess import check_output, run
import sys

TOOL = Path(__file__).resolve()
sys.path.insert(0, str(TOOL.parent))
from PlanarRegistryBuild import ROOT, bind, file_sha, load, require, write


BASE = "19e2e99aa8269dd0687e7edd332ca16671982190"
GROUP_RECEIPT = "9c876ad6f44156344334890b560cd839102c3db88dfe4441b0e446c7f089d063"
LABEL_RECEIPT = "d7af26b1562ee516f24b1476ef95a0142ff5d22f685106cfa33e72bb96ed6d94"
PRIOR = "fb68f130ad521ca7473c6f3f239a71a276ccb2318c75586b1eb63de930965f55"


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def read_hash(value):
    return sha256(canonical(value)).hexdigest()


def observe_archive(bundle, ordered_rules, present):
    from PlanarRootProjection import MATES, ReadMatesMut, ReadNativeName, SldprtArchive, WriteMatesMut
    from PlanarRootProjection import keyword_rows, owned_root, root_system

    archive = SldprtArchive.from_bytes(bundle.BytesValue)
    link, model, owners, lights, notes = owned_root(archive, present=present)
    graph = ReadMatesMut(archive.require(MATES), link.ResolvedValue)
    replay, _ = WriteMatesMut(graph.RootsValue, link.ResolvedValue)
    require(replay == archive.require(MATES), "generated complete ordered mate list does not replay exactly")
    require(tuple(ReadNativeName(node) for node in graph.RootsValue) == ordered_rules,
            "generated native membership differs from its ordered neutral owners")
    refs = owners["occurrence_alias"]
    signature = [{"name": ReadNativeName(node), "fields": {
        name: node.FieldsValue[name] for name in ("f3c0", "f3e8", "f3f0", "f3f4", "f3f8", "f400", "f408")
    }} for node in refs]
    result = {
        "model_name": ReadNativeName(model), "system": root_system(owners, lights, notes),
        "keyword_rows": keyword_rows(archive, owners),
        "mate_ids": [node.FieldsValue["f08"] for node in graph.RootsValue],
        "ordered_mates": list(ordered_rules),
        "occurrences": signature,
        "member_clocks": {"lights": [asdict(item.CreatedValue) for item in lights],
                          "notes": [asdict(notes.HeadCreated), asdict(notes.EndCreated)] if notes else []},
        "mate_round_trip": {"bytes": len(replay), "sha256": sha256(replay).hexdigest()},
    }
    return result


def worker():
    bind(ROOT)
    from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

    audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
    sys.addaudithook(audit.InspectEvent)

    def guard_network(event, args):
        if event.startswith(("socket.", "ctypes.")):
            audit.DeniedReads.append(event)
            raise PermissionError("assembly construction attempted a network or vendor operation")

    sys.addaudithook(guard_network)
    from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.MakePlanarGroup import MakePlanarGroup
    from convert.adapters.solidworks.Core.AssemblyPreparation.PlanAsmWrite import PlanAsmWrite
    from interchange.serialization.Deserialize import FromData
    from CheckOriginalPlanarMethod import no_recorded_state
    from PlanarRootProjection import prepare_system
    from ProveSketchLabelIntent import audit_link
    from SketchLabelIntent import make_group

    payload = json.load(sys.stdin)
    require(set(payload) == {"document", "labels", "native_parent", "event", "parent_system"},
            "research composition requires neutral geometry, the owned root system and a new locator")
    no_recorded_state(payload)
    document = FromData(payload["document"])
    require(not any(key.startswith("kit.research_") for key in document.metadata),
            "research source status cannot enter the neutral constructor")
    for name in (
        "RectanglePresentation",
        "convert.adapters.solidworks.Archive.Config.WriteConfigMut",
        "convert.adapters.solidworks.Archive.Resolved.WriteResolMut",
        "convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadLineDims",
        "interchange.document.Behavior.DocumentIo", "interchange.document.Models.DocumentProvenance",
        "interchange.document.Validation.DocumentValidate", "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate", "interchange.document.Validation.DocumentReferenceValidate",
    ):
        import_module(name)
    for name in ("utf-16-le", "utf-8", "utf-8-sig", "latin-1", "ascii"):
        lookup(name)
    document.assert_valid()
    audit.BeginBuild()
    portable = make_group(document, payload["native_parent"], payload["event"], payload["labels"])
    plan = PlanAsmWrite(document, payload["native_parent"], payload["event"])
    root = replace(plan.RootRecipe, SystemValue=prepare_system(plan.RootRecipe.SystemValue,
                                                              payload["parent_system"], payload["event"]))
    generated = MakePlanarGroup(portable.ChildValue, root, plan.Occurrences, plan.MatesValue, plan.FixedIndex)
    require(generated.ChildValue is portable.ChildValue, "parent state transfer rebuilt or exchanged the actual child")
    (group,) = document.assembly.mate_groups
    by_id = {row.id: row for row in document.assembly.mates}
    ordered_rules = tuple(by_id[identity].name for identity in group.mate_ids)
    before, after = (observe_archive(portable, ordered_rules, False), observe_archive(generated, ordered_rules, True))
    result = {"default": before, "generated": after, "baseline_streams": {
        name: sha256(data).hexdigest() for name, data in portable.StreamsValue.items()
    }, **audit_link(generated)}
    forbidden = [name for name in sys.modules if name == "Swapp" or name == "pythoncom" or name.startswith("win32com")]
    require(not forbidden and not audit.DeniedReads, "the composition worker crossed its no-input boundary")
    print(json.dumps({**result, "pid": os.getpid(), "runtime_input_reads": len(audit.DeniedReads),
                      "cad_imports": forbidden}, sort_keys=True, allow_nan=False))


def dispatch(request, rejection=None):
    result = run((sys.executable, "-I", "-B", str(TOOL), "--worker"), input=canonical(request),
                 capture_output=True, check=False, timeout=120)
    if rejection is not None:
        require(result.returncode != 0 and not result.stdout and rejection in result.stderr.decode()
                and b"PermissionError" not in result.stderr, "a negative refused at another stage")
        return rejection
    require(result.returncode == 0, result.stderr.decode(errors="replace"))
    row = json.loads(result.stdout)
    require(row["runtime_input_reads"] == 0 and row["cad_imports"] == [], "the worker was not a guarded independent writer")
    return row


def stream_comparison(run, system, source, expected, baseline_child, event):
    from ProveSketchLabelIntent import confirm
    from PlanarRootProjection import VISUALS

    confirm(run["actual"], expected)
    require(canonical(run["generated"]["system"]) == canonical(system),
            "generated typed owners differ from the decoded authored presentation")
    require(run["default"]["occurrences"] == run["generated"]["occurrences"]
            and run["default"]["ordered_mates"] == run["generated"]["ordered_mates"],
            "parent presentation transfer changed an occurrence or mate relationship")
    child = {row["id"]: row for row in source["keyword_owner_rows"]}
    joined = {}
    for key, row in (("source", list(child.values())), ("generated", run["generated"]["keyword_rows"])):
        joined[key] = {
            (item["owner"], item["order_within_owner"]): (item["class"], item["name"], item["keyword_tag"], item["keyword_type"])
            for item in row
        }
    require(joined["source"] == joined["generated"], "generated keyword entries lost an owner or presentation name")
    public_order = {
        key: [(item["owner"], item["order_within_owner"]) for item in rows]
        for key, rows in (("source", source["keyword_owner_rows"]), ("generated", run["generated"]["keyword_rows"]))
    }
    require(run["child"] == baseline_child, "root-system projection changed the previously proved generated child")
    require(VISUALS not in run["parent"]["streams"], "the scoped constructor unexpectedly published the separate visual store")
    clocks = run["generated"]["member_clocks"]
    timestamps = [{"SecondsValue": event, "FractionTicks": ordinal} for ordinal in range(1, 7)]
    require(clocks == {"lights": timestamps[:4], "notes": timestamps[4:]},
            "generated feature times did not derive from the new event and member order")
    changed = [name for name, digest in run["baseline_streams"].items() if run["parent"]["streams"][name]["sha256"] != digest]
    return {"changed_parent_streams": sorted(changed), "identical_parent_stream_set":
            set(run["baseline_streams"]) == set(run["parent"]["streams"]),
            "exact_owner_order_in_resolved_and_child_lists": True, "exact_keyword_row_order": public_order["source"] == public_order["generated"],
            "keyword_role_order": public_order, "keyword_rows_mapped": len(joined["source"]),
            "identical_child": True, "owned_xyz_and_centerline_labels": True,
            "fresh_member_clocks": clocks, "source_visual_states_emitted": False}


def prove(disclosed, output):
    bind(ROOT)
    from convert.adapters.solidworks.Archive.Construction.Assembly.CheckAsmMeta import CheckAsmMeta
    from convert.adapters.solidworks.Core.AssemblyPreparation.PlanAsmWrite import PlanAsmWrite
    from convert.adapters.solidworks.Core.AssemblyWriting.CheckAsmShape import CheckAsmShape
    from interchange import CadDocument
    from CheckOriginalPlanarMethod import no_recorded_state
    from PlanarPriorAdmission import source_intent
    from PlanarRootProjection import project
    from PlanarSourceLabels import project_labels
    from ProvePlanarMateGroup import checked, source_cases
    from ProvePlanarSourceLabels import reconstruct, refusal, strict_read
    from ProveSketchLabelIntent import payload, predict, send

    base_ref = ("git", "rev-parse", BASE + ":src")
    require(not check_output(("git", "diff", BASE, "--", "src", "tests"), cwd=ROOT),
            "source root experiment requires the original pinned SDK and guard")
    sdk_tree = check_output(base_ref, cwd=ROOT, text=True).strip()
    measures = ROOT / "re/solidworks/measurements/2026"
    groups = load(measures / "SdkPlanarMateGroupRead01.json", GROUP_RECEIPT)
    label_proof = load(measures / "SdkPlanarSourceLabelBridge01.json", LABEL_RECEIPT)
    prior = load(measures / "SdkPlanarPriorSourceAdmission01.json", PRIOR)
    require(groups["passed"] and label_proof["label_projection_passed"]
            and prior["raw_source_and_record_identities_preserved"],
            "required independently measured antecedents differ")
    output.mkdir()
    reports = {}
    all_pids = []
    for case in source_cases(disclosed):
        slot = case["case"]
        parent, child = (Path(case[role]) for role in ("parent", "child"))
        parent_raw = checked(parent, case["parent_sha256"])
        child_raw = checked(child, case["child_sha256"])
        author = json.loads(checked(parent.parent / "Record.json", case["native_record_sha256"]))
        fresh, read_stdout = strict_read(parent, case["parent_sha256"])
        source = CadDocument.from_json(fresh["document_json"])
        neutral, intent = source_intent(source, author["job"]["case"], child_raw)
        labels, origins = project_labels(source.assembly.documents[0].document, child_raw,
                                         neutral.assembly.documents[0].document, prior["cases"][slot]["exact_source_display"])
        require(canonical(labels) == canonical(label_proof["cases"][slot]["neutral_labels"]),
                "source transfer changed the previously guarded owned child labels")
        source_system = intent["source_intent"]["assembly"]["system"]
        system, audit = project(source, neutral, parent_raw, source_system)
        directory = output / slot
        directory.mkdir()
        custody = reconstruct(source, fresh["document_json"], neutral, directory)
        request = {**payload(neutral, labels), "parent_system": system}
        no_recorded_state(request)
        serialized = canonical(request)
        require(case["parent_sha256"].encode() not in serialized and case["child_sha256"].encode() not in serialized,
                "source-native evidence crossed into the constructor request")
        write(directory / "NeutralRequest.json", request)
        gate = refusal(CheckAsmShape, (source,), "assembly root contains unprojected model content")
        plan = PlanAsmWrite(neutral, request["native_parent"], request["event"])
        native_alias_guard = refusal(CheckAsmMeta, (replace(plan.RootRecipe, NameValue=audit["native_model_name"]),),
                                     "assembly self filename must match its actual authored name and assembly kind")
        original_group, = source.assembly.mate_groups
        bad_group = replace(source, assembly=replace(source.assembly, mate_groups=(
            replace(original_group, mate_ids=tuple(reversed(original_group.mate_ids))),
        )))
        crossed = refusal(project, (bad_group, neutral, parent_raw, source_system),
                           "the ordinary source group differs from its actual ordered typed members")
        bad_status = replace(source, metadata={**source.metadata, "kit.research_read_status": "unqualified"})
        status = refusal(project, (bad_status, neutral, parent_raw, source_system),
                          "research source status is outside the strict source projection")
        baseline, _, _ = send(payload(neutral, labels))
        first, second = (dispatch(request) for val in range(2))
        require({key: value for key, value in first.items() if key != "pid"}
                == {key: value for key, value in second.items() if key != "pid"}, "the model-only root composition is nondeterministic")
        comparisons = stream_comparison(first, system, audit, predict(neutral.assembly.documents[0].document, labels),
                                        baseline["child"], request["event"])
        bad_request = {**request, "parent_system": {**system, "source_manager_records": []}}
        forbidden = dispatch(bad_request, "a planar source system request has unsupported members or an unowned event")
        all_pids.extend((fresh["worker_pid"], baseline["pid"], first["pid"], second["pid"]))
        source_lock = label_proof["cases"][slot]["original_sha256"]
        require(source_lock == {"parent": case["parent_sha256"], "child": case["child_sha256"],
                                "author": case["native_record_sha256"]}, "source-packet custody differs")
        reports[slot] = {
            "original_locks": source_lock, "root_audit": audit,
            "full_private_custody": custody, "strict_reader_stdout_sha256": read_stdout,
            "guarded_request_sha256": read_hash(request), "guards": {"whole_source": gate, "binary_name_vs_self_name": native_alias_guard,
            "crossed_native_membership": crossed, "research_status": status, "unsupported_writer_field": forbidden},
            "generated_comparison": comparisons, "target_system": first["generated"], "label_source_owners": origins,
            "generated_artifacts": {"parent": first["parent"], "child": first["child"]},
            "guarded_builder_pids": [baseline["pid"], first["pid"], second["pid"]],
        }
        checked(parent, case["parent_sha256"])
        checked(child, case["child_sha256"])
    require(len(set(all_pids)) == len(all_pids), "independent guarded worker processes were reused")
    require(not check_output(("git", "diff", BASE, "--", "src", "tests"), cwd=ROOT), "the pinned SDK changed during the proof")
    return {
        "schema": "kit.sw2026.planar-source-root-owners.v1", "task": "B04-SW2026-MATES-PLANAR/source-root-projection",
        "owner": "assembly_frontier", "pr": 121, "base_revision": BASE, "sdk_tree": sdk_tree,
        "prior_group_receipt_sha256": GROUP_RECEIPT, "prior_labels_receipt_sha256": LABEL_RECEIPT,
        "prior_source_receipt_sha256": PRIOR, "passed": True, "source_system_and_ordered_mates_projected": True,
        "whole_source_admission": False, "new_native_runs": 0, "new_heldout_credit": 0, "runtime_input_reads": 0,
        "published_cad_files": 0, "successful_processes": len(all_pids), "guarded_refusal_processes": len(reports),
        "program_source_manifest": source_manifest(), "cases": reports,
    }


def source_manifest():
    paths = (
        "planar_registry/PlanarRootProjection.py", "planar_registry/ProvePlanarRootProjection.py",
        "planar_registry/PlanarPriorAdmission.py", "planar_registry/ProvePlanarMateGroup.py",
        "planar_registry/PlanarSourceLabels.py", "planar_registry/ProveSketchLabelIntent.py",
        "planar_registry/SketchLabelIntent.py", "OriginPortableWire.py", "ReadSdkOrderedNative.py",
        "para/concentric/ProveConcentricParentLights.py", "para/concentric/ProveConcentricParentNotes.py",
        "para/concentric/ProveConcentricParentExploded.py",
    )
    return {path: file_sha(ROOT / "re/tooling/sw2026" / path) for path in paths}


def sanitize(raw):
    cases = {}
    for name, row in raw["cases"].items():
        root = row["root_audit"]
        source = root["keyword_owner_rows"]
        target = row["target_system"]["keyword_rows"]
        comparison = row["generated_comparison"]
        custody = row["full_private_custody"]
        cases[name] = {
            "source_locks": row["original_locks"],
            "source_root_model_name": root["native_model_name"],
            "source_root_file_stem": root["public_root_name"],
            "source_configuration": root["configuration"],
            "source_configuration_reference": root["native_config_reference"],
            "source_diagnostics": root["source_diagnostics"],
            "source_member_counts": root["root_owner_counts"],
            "root_payload": root["retained_mates"],
            "owned_group_projection": root["source_group"],
            "source_clock_evidence": root["source_clocks"],
            "native_keyword_id_order": [item["id"] for item in source],
            "strict_source_root_order": [item["id"] for item in sorted(source, key=lambda item: item["public_order"])],
            "generated_keyword_id_order": [item["id"] for item in target],
            "source_to_target_keyword_owner_ids": [
                [item["id"], next(generated["id"] for generated in target
                    if (generated["owner"], generated["order_within_owner"])
                    == (item["owner"], item["order_within_owner"]))]
                for item in source
            ],
            "unconsumed_root_owners": root["unconsumed_owner_domains"],
            "source_guards": row["guards"],
            "generated_comparison": {key: value for key, value in comparison.items() if key != "keyword_role_order"},
            "original_wire_round_trip": {name: custody[name] for name in (
                "private_custody_sha256", "source_wire_sha256", "source_child_wire_sha256",
                "complete_source_wire_restored_exactly", "complete_source_child_wire_restored_exactly",
            )},
            "neutral_request_sha256": row["guarded_request_sha256"],
            "generated_artifacts": {role: {key: info[key] for key in ("bytes", "sha256")}
                                    for role, info in row["generated_artifacts"].items()},
        }
    return {**raw, "cases": cases}


def main():
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--disclosed", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        worker()
    else:
        require(args.disclosed is not None and args.output is not None, "previously disclosed share and private output are required")
        disclosed = args.disclosed.resolve(strict=True)
        output = args.output.resolve()
        require(not output.exists() and not output.is_relative_to(ROOT) and not output.is_relative_to(disclosed),
                "choose a fresh private output directory outside the repository and disclosed input")
        report = prove(disclosed, output)
        write(output / "PrivateResult.json", report)
        print(write(output / "Receipt.json", sanitize(report)))


if __name__ == "__main__":
    main()
