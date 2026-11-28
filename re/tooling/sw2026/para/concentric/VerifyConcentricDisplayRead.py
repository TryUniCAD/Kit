import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from xml.etree.ElementTree import SubElement, register_namespace, tostring


REPO = Path(__file__).resolve().parents[5]
SW2026 = REPO / "re/tooling/sw2026"
sys.path[:0] = [str(REPO / "src"), str(SW2026), str(SW2026 / "serial")]

from convert.adapters.solidworks.Assembly.Assembly import XmlRoot
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from para.concentric.AuditConcentricDisplayState import INSTANCE, VISUAL, children, published_cases
from para.concentric.ProveConcentricSourceBrep import D01_LOCKED, RADIAL_LOCKED, checked, require
from para.concentric.ProveSignedConcentricWriter import inventory_receipt, source_inventory


BASELINE = "dcfa8476bc1323ce0d6ee32b86b1b1b446ddf6a5"
TOOL = "re/tooling/sw2026/para/concentric/VerifyConcentricDisplayRead.py"
SCOPE = ("Assembly/Assembly.py", "Core/Adapter.py", "Assembly/Display/DisplayMember.py",
         "Assembly/Display/DisplayOwner.py", "Assembly/Display/ReadDisplayXml.py",
         "Assembly/Display/CheckDisplay.py", "Assembly/Display/ReadAsmDisplay.py", "Assembly/Display/DisplayData.py")
AUDIT = "6d2e2dcddbaf2db31696cd925e0d8e360947ee29db739a8b7a1cdb9c0c98c944"
TYPED_KEY = "typed_display_states"
SEMANTIC_KEY = "solidworks_source_semantic_sha256"
NS = "http://www.solidworks.com/sw2003/schema"
WORKER = """
from dataclasses import replace
import json
from pathlib import Path
import sys
root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root / "src"))
import convert
from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Core.Adapter import SemanticShaTwo
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.ReadAsmModel import ReadAsmModel
from convert.api.ApiContext import KConvertEngine
from interchange import frozen_mapping
from interchange.serialization.EncodeData import ToData
assert Path(convert.__file__).resolve().is_relative_to(root / "src")
result = {}
for label, path, resolve in json.load(sys.stdin):
    try:
        if resolve:
            doc = convert.open_document(Path(path), strict=True, include_brep=False, include_tessellation=False)
        else:
            doc = KConvertEngine.read(Path(path), options=ReadOptions(
                strict=True, include_brep=False, include_tessellation=False, values={"resolve_components": False}))
        doc.assert_valid()
    except (ValueError, TypeError, KeyError) as error:
        result[label] = {"read_refusal": [type(error).__name__, str(error)]}
        continue
    try:
        ReadAsmModel(doc)
    except ValueError as error:
        write_guard = str(error)
    else:
        raise ValueError("ordinary reader unexpectedly cleared generic writer admission")
    attributes = dict(doc.assembly.attributes)
    typed = attributes.pop("typed_display_states", None)
    raw = doc if typed is None else replace(doc, assembly=replace(doc.assembly, attributes=frozen_mapping(attributes)))
    result[label] = {"document": ToData(doc), "generic_writer_guard": write_guard, "typed_display_states": typed,
                     "computed_fingerprint": SemanticShaTwo(doc), "unextended_fingerprint": SemanticShaTwo(raw)}
print(json.dumps(result, sort_keys=True, allow_nan=False))
"""


def digest(value):
    return sha256(value).hexdigest()


def json_digest(value):
    return digest(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def region(tree):
    config, = children(children(tree, "swConfigurationList")[0], "swConfiguration")
    listing, = children(config, "swDisplayStateList")
    state, = children(listing, "swDisplayState")
    model, = (row for row in children(children(tree, "swModelList")[0], "swModel") if row.attrib["id"] == config.attrib["swModelRef"])
    return config, listing, state, model, children(model, "swReference")


def xml_variants(base, empty):
    register_namespace("", NS)
    edits = {
        "mixed_polarity": ("state", "swShowState", "Yes,No,"),
        "hidden_conflict": ("first_ref", "swHidden", "YES"),
        "unknown_action": ("state", "swShowState", "Yes,YES,"),
        "short_action_vector": ("state", "swShowState", "Yes,"),
        "xml_occurrence_ids_as_members": ("list", "swCompNameList", "4,7,"),
        "reordered_members": ("list", "swCompNameList", "25,24,"),
        "duplicate_members": ("list", "swCompNameList", "24,24,"),
        "foreign_config_id": ("config", "swID", "1"),
        "foreign_config_name": ("config", "swName", "UnresolvedDisplayConfig"),
        "foreign_root_name": ("config", "swReference", "UnresolvedDisplayRoot"),
        "object_id_collision": ("list", "id", "7"),
        "false_object_count": ("root", "swObjCount", "10"),
    }
    variants = {}
    for name, (node, attr, value) in edits.items():
        tree = XmlRoot(base.require(INSTANCE))
        config, listing, state, model, occurrences = region(tree)
        {"root": tree, "config": config, "list": listing, "state": state, "first_ref": occurrences[0]}[node].set(attr, value)
        variants[name] = (base, tostring(tree, encoding="utf-8"))
    tree = XmlRoot(base.require(INSTANCE))
    config, listing, _, _, occurrences = region(tree)
    occurrences[0].set("swID", "31")
    listing.set("swCompNameList", "31,25,")
    variants["xml_consistent_foreign_binary_occurrence"] = (base, tostring(tree, encoding="utf-8"))
    tree = XmlRoot(base.require(INSTANCE))
    config, listing, _, _, _ = region(tree)
    config.remove(listing)
    tree.append(listing)
    variants["detached_list"] = (base, tostring(tree, encoding="utf-8"))
    tree = XmlRoot(empty.require(INSTANCE))
    top = SubElement(tree, f"{{{NS}}}swDisplayStateList", {"swObjCount": "2"})
    SubElement(top, f"{{{NS}}}swDisplayState", {"id": "4", "swDisplayStateName": "Current State", "swName": "Older Name"})
    SubElement(top, f"{{{NS}}}swDisplayState", {"id": "5", "swName": "Legacy State"})
    tree.set("swObjCount", "5")
    variants["legacy_names"] = (empty, tostring(tree, encoding="utf-8"))
    return variants


def run_worker(root, jobs):
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", WORKER, str(root)],
        input=json.dumps(jobs), capture_output=True, text=True, check=True, timeout=100,
    )
    return json.loads(result.stdout)


def typed_expected(row):
    index = row["xml"]
    state = index["state"]
    if state is None:
        return None
    config_object_id, config_id, config_name = index["configuration"]
    refs = {ref["feature_id"]: ref["xml_id"] for ref in index["occurrences"]}
    return [{"configuration_object_id": config_object_id, "configuration_id": config_id,
             "configuration_name": config_name, "model_object_id": index["root_model_id"],
             "list_object_id": state["list_id"], "state_object_id": state["id"], "name": state["name"],
             "visibility": [{"native_object_id": refs[feature], "native_feature_id": feature, "visible": action == "Yes"}
                            for feature, action in state["members"]]}]


def main():
    parser = argparse.ArgumentParser(description="Verify the bounded SDK assembly display-state read projection")
    parser.add_argument("disclosed_root", type=Path)
    parser.add_argument("prior_source_closure", type=Path)
    parser.add_argument("new_scratch", type=Path)
    args = parser.parse_args()
    before = source_inventory(args.prior_source_closure)
    after = source_inventory(REPO)
    changed = {name for name in set(before) | set(after) if before.get(name) != after.get(name)}
    prefix = "src/convert/adapters/solidworks/"
    require(changed == {TOOL, *(prefix + path for path in SCOPE)}, "display-read proof is outside the exact source overlay")
    audit = json.loads(checked(REPO / "re/solidworks/measurements/2026/ConcentricDisplayState01.json", AUDIT))["cases"]
    out = args.new_scratch.resolve()
    out.mkdir()
    base = args.disclosed_root.resolve()
    d01 = base / "ConcentricMateSourcePacket02/Disclosed/D01"
    lock = json.loads(checked(d01 / "lock.json", "bdd8bf3782ccf01991a3ac402da2923f2d320728792fb8ccb500f73189e9f90b"))
    require(lock["source_locked"] and not lock["heldout_source_locked"], "only the disclosed D01 closure is admitted")
    own = (
        ("D01", d01 / "Native", D01_LOCKED, "ConcentricD01AlignedFree.SLDASM", "ConcentricD01Child.SLDPRT"),
        ("Radial", base / "RadialConcentric01", RADIAL_LOCKED, "RadialConcentricProbe.SLDASM", "DisclosedRadialSceneProbe.SLDPRT"),
    )
    files = {name + role: (top / role / parent, h[0]) for name, top, group, parent, _ in own for role, h in group.items()}
    linked_children = [(top / role / child, h[1]) for _, top, group, _, child in own for role, h in group.items()]
    files.update((label, (path, sha)) for label, path, sha, *_ in published_cases())
    payloads = {label: checked(path, sha) for label, (path, sha) in files.items()}
    require(all(files[label][1] == row["native_sha256"] for label, row in audit.items()), "independent evidence hashes differ")
    for path, sha in linked_children:
        checked(path, sha)
    jobs = [(name, str(path), False) for name, (path, _) in files.items()]
    expected = {name: typed_expected(audit[name]) for name in files}
    for label, _, group, _, _ in own:
        for role in group:
            name = label + role
            full = name + "Resolved"
            jobs.append((full, str(files[name][0]), True))
            expected[full] = expected[name]
    archive = SldprtArchive.from_bytes(payloads["D01Source"])
    empty = SldprtArchive.from_bytes(payloads["A12SyncedEmpty"])
    controls = {label: (dict(origin.streams) | {INSTANCE: xml}, origin.format_version, None)
                for label, (origin, xml) in xml_variants(archive, empty).items()}
    for label, visual_value in (("visual_store_omitted", None), ("visual_store_unreadable", b"invalid visual cache")):
        streams = dict(archive.streams)
        if visual_value is None:
            del streams[VISUAL]
        else:
            streams[VISUAL] = visual_value
        controls[label] = (streams, archive.format_version, expected["D01Source"])
    diagnostic_hashes = {}
    for label, (streams, version, wanted) in controls.items():
        folder = out / label
        folder.mkdir()
        path = folder / ("A12SyncedEmpty.SLDASM" if label == "legacy_names" else files["D01Source"][0].name)
        data = BuildSldprt(streams, FormatVersion=version)
        path.write_bytes(data)
        diagnostic_hashes[label] = digest(data)
        jobs.append((label, str(path), False))
        expected[label] = wanted
    prior = run_worker(args.prior_source_closure, jobs)
    newer = run_worker(REPO, jobs)
    rows = {}
    for label, _, _ in jobs:
        older = prior[label]
        fresh = newer[label]
        if "read_refusal" in older:
            require(label in diagnostic_hashes and expected[label] is None and fresh == older,
                    "generic read refusal changed: " + label)
            rows[label] = older
            continue
        require("document" in older and "document" in fresh, "generic reader refused diagnostic or disclosed assembly: " + label)
        attributes = fresh["document"]["assembly"]["attributes"]
        typed = fresh.pop(TYPED_KEY)
        attributes.pop(TYPED_KEY, None)
        require(typed == expected[label], "typed ownership differs: " + label)
        old_stamp = older["document"]["metadata"][SEMANTIC_KEY]
        new_stamp = fresh["document"]["metadata"][SEMANTIC_KEY]
        require(older.pop("computed_fingerprint") == old_stamp and fresh.pop("computed_fingerprint") == new_stamp
                and older.pop("unextended_fingerprint") == fresh.pop("unextended_fingerprint") == old_stamp
                and (new_stamp != old_stamp) == (typed is not None),
                "admitted view does not explain the dependent source fingerprint: " + label)
        fresh["document"]["metadata"][SEMANTIC_KEY] = old_stamp
        require(older.pop(TYPED_KEY) is None and json_digest(fresh) == json_digest(older),
                "raw assembly values or generic writer refusal changed: " + label)
        raw = attributes["display_states"]["$tuple"]
        if label == "legacy_names":
            require([row["name"] for row in raw] == ["Current State", "Legacy State"], "legacy name precedence changed")
        rows[label] = {"full_raw_document_sha256": json_digest(older["document"]), "typed_display_states": typed,
                       "generic_writer_guard": older["generic_writer_guard"], "raw_leaf_row_count": len(raw),
                       "source_semantic_sha256_before_after": [old_stamp, new_stamp]}
    for path, sha in (*files.values(), *linked_children):
        checked(path, sha)
    require(source_inventory(args.prior_source_closure) == before and source_inventory(REPO) == after, "observed source closure changed")
    report = {"schema": "kit.sw2026.qualified-assembly-display-read.v1", "baseline": BASELINE,
              "baseline_audit_sha256": AUDIT, "before": inventory_receipt(before), "after": inventory_receipt(after),
              "changed_sources_sha256": {path: after[path] for path in sorted(changed)},
              "cases": rows, "diagnostic_sha256": diagnostic_hashes, "paired_full_document_comparisons": len(jobs),
              "public_writer_admission_changed": False, "visual_store_native_optional_proven": False,
              "native_processes": 0, "heldout_inputs_read": 0, "writer_outputs": 0, "passed": True}
    (out / "Receipt.json").write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
