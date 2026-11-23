from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from ProveD01PropertyTransport import CASE_MANIFESTS, REPO, checked, disclosed_cases, proof_guard, require, wire
from PrepareGeneratedConcentric import windows_path
from ProveSdkConcPlan import preload
from ProveSdkCylParent import CASES, create, parent
from AssemblyMateDescriptor import make_mate_descriptor
from Classes import registry
from Streams import StreamDoc, load_rooted, store_rooted

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
from convert.adapters.solidworks.Archive.Mates.WriteMatesMut import WriteMatesMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.serialization.Deserialize import FromData


BASE = "935d9848dab052aff0bc4495faa579e011cc7cba"
MODULE = "569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e"
PRIOR = "676fb1e7e56e929d880a7de1471acf7cb456b70f9fec862f00961fc597736c51"
STREAM = "SwDocContentMgr/SwDocContentMgrInfo"
CMGR = "Contents/CMgr"
MATES = "Contents/Config-0-MatesList"
VERSION = 19000


def fingerprint(raw):
    return sha256(raw).hexdigest()


def selected_config(manager):
    fields = manager.FieldsValue
    current = fields["f360"]
    require(current is fields["f368"] and len(fields["f370"]["items"]) == fields["f370"]["n"] == 1
            and fields["f370"]["items"][0]["o"] is current,
            "expected one actual active CMgr configuration")
    return current


def inventory(value):
    return {"bytes": len(value), "sha256": fingerprint(value)}


def descriptor_rows(document, config, root):
    index, = document.roots
    owner, = (row["o"] for row in index.f["f38"]["items"] if row["o"].cls == "moBCConfigurationInfo_c")
    require(index.cls == "moBCModeInfo_c" and not document.tail
            and owner.f["f08"] == ReadNodeName(config) and owner.f["f18"] == config.FieldsValue["f08"]
            and owner.f["f10"] == "ACTIVE" and owner.f["f20"].cls == "moBCConfigObjMapInfo_c",
            "content index differs from the actual active configuration")
    nodes = tuple(row["o"] for row in owner.f["f20"].f["f08"]["items"])
    model, = (row for row in nodes if row.f["f08"] == root.FieldsValue["f08"])
    require(model.cls == "moBCNode_c" and all(row is model or not row.f["f50"]["items"] for row in nodes),
            "mate list does not belong exclusively to the actual assembly model")
    rows = model.f["f50"]["items"]
    require(model.f["f50"]["n"] == len(rows)
            and all(row["o"].ClassValue == RuntimeClass("moBCMate_c", 1) for row in rows),
            "source contains an unsupported descriptor record")
    return rows


def inspect_source(path, pin, reg):
    archive = SldprtArchive.from_bytes(checked(path, pin))
    data = archive.require(STREAM)
    document, cursor = load_rooted(data, reg, 1, VERSION)
    require(store_rooted(document, reg, VERSION) == data, "typed source content index failed exact replay")
    link = ReadNativeLink(archive, 0)
    manager = ReadCmgrMut(archive.require(CMGR), VERSION).RootValue
    root = link.ConfigValue.RootValue
    config = selected_config(manager)
    mates = ReadMatesMut(archive.require(MATES), link.ResolvedValue).RootsValue
    require(WriteMatesMut(mates, link.ResolvedValue)[0] == archive.require(MATES)
            and WriteCmgrMut(manager, VERSION) == archive.require(CMGR),
            "live mate list or active configuration failed exact linked replay")
    rows = descriptor_rows(document, config, root)
    require(len(rows) == len(mates), "descriptor inventory does not match actual ordered mates")
    descriptors = []
    for row, mate in zip(rows, mates, strict=True):
        actual = row["o"]
        generated = make_mate_descriptor(root, config, mate)
        require(actual.f == generated.f, "independently built mate fields differ from the saved descriptor")
        descriptors.append({
            "node_id": generated["f3c"], "mate_type": generated["f24"], "concrete_class": generated["f28"],
            "descriptor_characters": len(generated["f30"]), "allocation": actual.index,
            "wire_bytes": actual.end - actual.pos,
        })
        row["o"] = generated
    require(store_rooted(document, reg, VERSION) == data,
            "replacing descriptor vertices with freshly derived records changed the content index")
    return {"source_sha256": pin, "content_index": inventory(data),
            "final_map_counter": cursor.count, "descriptors": descriptors, "replacement_exact": True}


def cases(disclosures, prior):
    base = disclosures / "ConcentricMateSourcePacket02/Disclosed"
    for case in disclosed_cases():
        slot = case["id"]
        for phase in ("Source", "Edited"):
            source = base / slot / "Native" / phase / (case["name"] + ".SLDASM")
            yield slot + "/" + phase, source, prior["disclosed_sources"][slot][phase]["source_sha256"]
    for folder, (_, names) in CASE_MANIFESTS.items():
        for name in names:
            source = REPO / "re/solidworks/v2026/corpus" / folder / name
            yield name, source, prior["independent_assembly_controls"][name]["source_sha256"]


def contrast(document):
    graph = document.assembly
    alternate = "Mechanism Review"
    labels = ("Motion-guide-17", "Other-mount-3")
    instances = tuple(replace(row, name=label) for row, label in zip(graph.instances, labels, strict=True))
    definitions = tuple(replace(row, configuration_name=alternate) if row.id == graph.root_definition_id else row
                        for row in graph.definitions)
    mate, = graph.mates
    changed = replace(mate, name="Opposite axis 検", entity_ids=mate.entity_ids[::-1],
                      attributes={"rotation_locked": True})
    return replace(document, configurations=(replace(document.configurations[0], name=alternate),),
                   assembly=replace(graph, definitions=definitions, instances=instances, mates=(changed,)))


def require_refusal(action, expected):
    try:
        action()
    except ValueError as error:
        require(expected in str(error), "unexpected descriptor guard: " + str(error))
        return str(error)
    raise ValueError("invalid graph reached the content-index mate descriptor")


def check_refusals(result):
    root, config = result.StateValue.RootValue, result.StateValue.CurrentConfig
    mate, = result.MateValues
    fields = mate.FieldsValue
    first, second = (row["o"] for row in fields["f410"])
    orphan = ArchiveNode(first.ClassValue, dict(first.FieldsValue, f74=fields["f08"] + 1))
    reused = ArchiveNode(second.ClassValue, dict(first.FieldsValue, f7c=1))
    slot = ArchiveNode(second.ClassValue, dict(second.FieldsValue, f7c=0))
    stale_config = ArchiveNode(config.ClassValue, dict(config.FieldsValue, f420=[{"key": fields["f08"], "o": None}]))
    wrong_group = ArchiveNode(RuntimeClass("moMateGroup_c", 1), {"owner": first})

    def with_ends(one, two):
        return ArchiveNode(mate.ClassValue, dict(fields, f410=[{"o": one}, {"o": two}]))

    return {
        "crossed_wrapper_owner": require_refusal(lambda: make_mate_descriptor(root, config, with_ends(orphan, second)),
                                                  "ordered active wrapper allocation"),
        "wrong_endpoint_slot": require_refusal(lambda: make_mate_descriptor(root, config, with_ends(first, slot)),
                                               "ordered active wrapper allocation"),
        "reused_end": require_refusal(lambda: make_mate_descriptor(root, config, with_ends(first, reused)),
                                       "distinct actual endpoint owners"),
        "configuration_override": require_refusal(lambda: make_mate_descriptor(root, stale_config, mate),
                                                  "configuration without overrides"),
        "foreign_mate_group": require_refusal(lambda: make_mate_descriptor(
            root, config, ArchiveNode(mate.ClassValue, dict(fields, owner=wrong_group))), "ordinary active two-end mate"),
        "unclassified_type": require_refusal(lambda: make_mate_descriptor(
            root, config, ArchiveNode(RuntimeClass("moMateParallel", 1), fields)), "unclassified concrete mate type"),
    }


def observed_generation(result, reg):
    mate, = result.MateValues
    state = result.StateValue
    config = selected_config(state.ManagerValue)
    require(config is state.CurrentConfig, "projection lost the actual generated assembly configuration")
    value = make_mate_descriptor(state.RootValue, config, mate)
    fragment = store_rooted(StreamDoc("descriptor", {"base": 1}, [value]), reg, VERSION)
    decoded, _ = load_rooted(fragment, reg, 1, VERSION)
    node, = decoded.roots
    require(node.f == value.f and not decoded.tail and store_rooted(decoded, reg, VERSION) == fragment,
            "descriptor's model-only archive failed exact reread")
    return {"parent": inventory(result.BytesValue), "child": inventory(result.ChildValue.BytesValue),
            "fragment": inventory(fragment), "fields": value.f}


def worker(request):
    require(set(request) == {"document", "ambient", "destination", "epoch"},
            "worker accepts only the authored part, assembly and destination inputs")
    original = FromData(request["document"])
    changed = contrast(original)
    for document in (original, changed):
        preload(document)
    reg = registry()
    attempted = proof_guard()
    reports = {}
    for label, document in (("ordinary", original), ("reversed_presentation", changed)):
        args = (document, None, request["ambient"], request["destination"], request["epoch"], None)
        result = parent(create("persistence", args), None, None)
        reports[label] = observed_generation(result, reg)
    require(reports["ordinary"]["fields"]["f30"] ==
            "ConcentricAuthored (NeutralCylinderAlphaDerived<1>,NeutralCylinderAlphaDerived<2>)"
            and reports["reversed_presentation"]["fields"]["f30"] == "Opposite axis 検 (Other-mount<3>,Motion-guide<17>)"
            and reports["reversed_presentation"]["fields"]["f08"] == "Mechanism Review"
            and reports["ordinary"]["child"] == reports["reversed_presentation"]["child"],
            "authored configuration, name or reversed selected-reference order was lost")
    reports["refusals"] = check_refusals(result)
    require(not attempted, "mate descriptor construction attempted runtime input access")
    return {"authored": reports, "runtime_input_accesses": len(attempted)}


def main():
    parser = ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--worker", action="store_true")
    mode.add_argument("--disclosures", type=Path)
    args = parser.parse_args()
    if args.worker:
        sys.stdout.buffer.write(wire(worker(json.load(sys.stdin))))
        return
    root = args.disclosures
    measurements = REPO / "re/solidworks/measurements/2026"
    prior = json.loads(checked(measurements / "ConcentricD01PropertyTransport01.json", PRIOR))
    reg = registry()
    decoded = {label: inspect_source(path, pin, reg) for label, path, pin in cases(root, prior)}
    packet, packet_pin = CASES["persistence"]
    folder = root / packet
    trial = json.loads(checked(folder / "Trial.json", packet_pin))

    def owned_evidence(role):
        key = "Evidence/" + role + ".json"
        return json.loads(checked(folder / key, trial["files_sha256"][key]))

    request = wire({"document": owned_evidence("Neutral"), "ambient": owned_evidence("Ambient"),
                    "destination": windows_path(folder / "Working" / trial["working_names"]["parent"]),
                    "epoch": owned_evidence("Build")["written_at"]})
    command = (sys.executable, "-I", "-B", str(HERE), "--worker")
    first, second = (subprocess.run(command, input=request, capture_output=True, timeout=180) for _ in range(2))
    require(first.returncode == second.returncode == 0 and first.stdout == second.stdout,
            (first.stderr + second.stderr).decode() or "guarded independent builds differ")
    generated = json.loads(first.stdout)
    require(all(generated["authored"]["ordinary"][role]["sha256"] == trial["generated_sha256"][role]
                for role in ("parent", "child")), "the prior qualified parent/child changed")
    result = {"schema": "kit.sw2026.assembly-mate-descriptor.v1", "base": BASE, "module_sha256": MODULE,
              "pinned_disclosure_receipt_sha256": PRIOR, "prior_generated_pair_trial_sha256": packet_pin,
              "request_sha256": fingerprint(request), "source_and_control_replacements": decoded,
              "guarded_generation": generated, "guarded_workers": 2,
              "native_runs": 0, "heldout_accesses": 0,
              "proof_source_sha256": {path.name: fingerprint(path.read_bytes()) for path in (
                  HERE, HERE.with_name("AssemblyMateDescriptor.py"))}}
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
