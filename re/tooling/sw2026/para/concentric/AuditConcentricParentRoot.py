import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO / "src"))

from convert import open_document
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, ReadNodeName, ReadRows, RequireNode, RequireRecord
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.CheckAsmRoot import CheckAsmRoot
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadLightInput import ReadLightInput
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadNotesInput import ReadNotesInput
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadChildren import ReadChildren
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

from hashlib import sha256


KNOWN = {
    "source": "2267cb6bc7e02d05be19ce5105ba3e43240eb4d1ad897647237dc875445d0dc2",
    "generated": "9474ca54466a450eec3ba5e49703053fe160e0a221647b2bcc984d8d3672dc74",
    "saved": "19d1b44bff684f0414549b5d997fba89f9e67368e20aac31d855c947e0e3a5a3",
    "native_receipt": "3263e7d2019953bede2c36948b84274d915b9cd8f4de1afc0bcb1988e0397f03",
}


def require(value, message):
    if not value:
        raise ValueError(message)


def sealed_bytes(path, role):
    require(not path.is_symlink(), "expected an actual disclosed file")
    payload = path.read_bytes()
    require(sha256(payload).hexdigest() == KNOWN[role], "the disclosed input hash differs: " + role)
    return payload


def light_intent(node):
    value = asdict(ReadLightInput(node))
    value.pop("CreatedValue")
    return value


def source_root(path, role):
    archive = SldprtArchive.from_bytes(sealed_bytes(path, role))
    document = open_document(path, include_brep=True, include_tessellation=False)
    linked = ReadNativeLink(archive, 0)
    model = linked.ConfigValue.RootValue
    ordered_roots = linked.ResolvedValue.RootsValue
    environment, = (node for node in ordered_roots if node.ClassValue.NameValue == "moEnvFolder_c")
    cabinet, = (node for node in ordered_roots if node.ClassValue.NameValue == "moDetailCabinet_c")
    require(environment is model.FieldsValue["f1e0"], "the actual configuration environment lacks its resolved identity")
    lights = ReadChildren(environment)
    notes = ReadChildren(cabinet)
    note_pair = ReadNotesInput(notes) if notes else None
    explosion = model.FieldsValue["f1590"]
    explosion_empty = None
    if explosion is not None:
        values = RequireNode(explosion, "moExplViewManager_c").FieldsValue
        explosion_empty = (values["f358"] is None and values["f360"] is None and values["f368"] == {"n": 0, "items": []}
                           and values["f398"] == 0.0 and values["f3a0"] == values["f3a4"] == -1)
        require(explosion_empty, "the source holds an authored or unsupported exploded-view owner")
    body_list = RequireRecord(RequireRecord(model.FieldsValue["f68"])["list"])
    references = tuple(RequireNode(row["o"], "moReference_c") for row in ReadRows(body_list["items"]))
    categories = {
        "resolved_root": ordered_roots, "environment_member": lights, "annotation_member": notes,
        "exploded_manager": (explosion,) if explosion is not None else (), "occurrence_alias": references,
    }
    native_owners = {FieldInt(node.FieldsValue, "f08"): (owner, node.ClassValue.NameValue)
                     for owner, rows in categories.items() for node in rows}
    require(len(native_owners) == sum(map(len, categories.values())), "a parent identity aliases unrelated owners")
    public = []
    for row in document.feature_timeline:
        persistent_id = row.attributes["native_object_id"]
        owner, kind = native_owners[persistent_id]
        public.append({"id": persistent_id, "name": row.name, "class": kind, "owner": owner})
    require(len(public) == len(native_owners) and {row["id"] for row in public} == set(native_owners),
            "the public root feature inventory and actual typed owners disagree")
    manager = ReadCmgrMut(archive.require("Contents/CMgr"), 19000).RootValue
    active = manager.FieldsValue["f360"]
    require(active is manager.FieldsValue["f368"] and ReadNodeName(active) == document.configurations[0].name,
            "public root configuration and independent manager selection disagree")
    defn = next(row for row in document.assembly.definitions if row.id == document.assembly.root_definition_id)
    try:
        CheckAsmRoot(document)
    except ValueError as error:
        refusal = str(error)
    else:
        raise ValueError("the whole-source admission guard unexpectedly opened")
    mate_report = document.metadata.get("solidworks.typed_mates_semantics", {})
    payloads = [{"format": row.format_id, "kind": row.kind, "attribute_names": sorted(row.attributes),
                 "declared_count": row.attributes.get("declared_count"), "records": len(row.attributes.get("records", ()))}
                for row in document.brep_payloads]
    require(len(payloads) == 1 and payloads[0]["format"] == "solidworks.mates" and payloads[0]["kind"] == "mate-list",
            "source payload is not the known retained mate representation")
    return {
        "input_sha256": KNOWN[role], "native_root_name": ReadNodeName(model), "public_root_name": defn.name,
        "configuration": ReadNodeName(active), "configuration_attribute_keys": sorted(document.configurations[0].attributes),
        "root_refusal": refusal, "native_and_public_feature_counts": [len(native_owners), len(public)],
        "archive_owner_counts": {name: len(rows) for name, rows in categories.items()}, "public_features": public,
        "diagnostic_codes": [row.code for row in document.diagnostics], "light_intent": [light_intent(node) for node in lights],
        "empty_notes_intent": [note_pair.HeadName, note_pair.EndName] if note_pair else None,
        "explicit_empty_exploded_manager": explosion_empty, "retained_payloads": payloads, "typed_mate_status": mate_report.get("status"),
        "typed_mate_diagnostic": mate_report.get("diagnostic"),
        "document_source_attribute_keys": sorted(document.source.attributes), "root_metadata_keys": sorted(document.metadata),
        "display_states": [{"name": row["name"], "native_attributes": dict(row["native_attributes"])}
                           for row in document.assembly.attributes["display_states"]],
    }


def main():
    parser = argparse.ArgumentParser(description="Audit the root-owner and retained-evidence boundary on the three disclosed concentric parents")
    for name in (*KNOWN, "output"):
        parser.add_argument("--" + name.replace("_", "-"), type=Path, required=True)
    args = parser.parse_args()
    receipt = json.loads(sealed_bytes(args.native_receipt, "native_receipt"))
    require(receipt["passed"] is True and receipt["phases"]["Generated"]["saved"]["parent"] == KNOWN["saved"],
            "the saved parent lacks its exact native lifecycle result")
    rows = {role: source_root(getattr(args, role), role) for role in ("source", "generated", "saved")}
    source, generated, saved = [rows[role] for role in ("source", "generated", "saved")]
    require(len(source["light_intent"]) == 4 and source["light_intent"] == saved["light_intent"]
            and source["empty_notes_intent"] == saved["empty_notes_intent"]
            and source["explicit_empty_exploded_manager"] is saved["explicit_empty_exploded_manager"] is True
            and not generated["light_intent"] and generated["empty_notes_intent"] is None
            and generated["explicit_empty_exploded_manager"] is None, "the disclosed cold/save difference changed")
    result = {"schema": "kit.sw2026.concentric-parent-root-audit.v1", "native_receipt_sha256": KNOWN["native_receipt"],
              "native_processes_started": 0, "heldout_inputs_read": 0, "source_admitted": False,
              "disclosed_default_members_match_after_native_save": True, "cases": rows}
    with args.output.open("x") as target:
        json.dump(result, target, indent=2, sort_keys=True, allow_nan=False)
        target.write("\n")
    print(json.dumps({role: (row["archive_owner_counts"], row["display_states"], row["typed_mate_status"]) for role, row in rows.items()}, sort_keys=True))


if __name__ == "__main__":
    main()
