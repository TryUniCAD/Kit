from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import sys
from zlib import ZLIB_RUNTIME_VERSION


ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "re"), str(ROOT / "re/automation")]

from EncoderRoundTrip.Source import decode_document
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Config.ReadPartConfig import ReadPartConfig
from convert.adapters.solidworks.Archive.Properties.ReadPropManager import ReadPropManager
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Properties.ReadLegacyEmptyProps import ReadLegacyProps
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.document.Models.DocumentModel import CadDocument
from tooling.sw2026.PreparePlainPartEvidence import construct


def digest(raw):
    return sha256(raw).hexdigest()


def outcome(action):
    try:
        return {"result": type(action()).__name__}
    except (ValueError, TypeError, KeyError) as error:
        return {"error_type": type(error).__name__, "refused": str(error)}


def stream_inventory(archive):
    return {
        row.name: {"bytes": len(clear), "sha256": digest(clear)}
        for row in archive.records
        for clear in (archive.require(row.name),)
    }


def feature_rows(document):
    return [
        {
            "id": item.id,
            "name": item.name,
            "kind": str(item.kind),
            "operation": str(item.operation),
            "owners": list(item.input_feature_ids),
            "selection_ids": list(item.selection_ids),
            "attribute_keys": sorted(item.attributes),
        }
        for item in document.feature_timeline
    ]


def inspected(raw, neutral_path):
    document, neutral, _ = decode_document(raw, "solidworks.sldprt")
    with neutral_path.open("xb") as stream:
        stream.write(neutral)
    archive = SldprtArchive.from_bytes(raw, "<comparison>")
    version = ContainerMo(archive.streams)
    streams = stream_inventory(archive)
    properties = archive.get("Contents/CusProps")
    part = next((body for body in document.bodies if body.topology.solid_count), None)
    return {
        "sha256": digest(raw),
        "bytes": len(raw),
        "neutral_sha256": digest(neutral),
        "container": archive.format_version,
        "archive_version": version,
        "streams": streams,
        "typed_reads": {
            "manager": outcome(lambda: ReadCmgrMut(archive.require("Contents/CMgr"), version)),
            "part_config": outcome(lambda: ReadPartConfig(archive)),
            "linked_model": outcome(lambda: ReadNativeLink(archive, 0)),
            "property_manager": None if properties is None else outcome(lambda: ReadPropManager(properties, version)),
            "legacy_property_profile": None if properties is None else outcome(lambda: ReadLegacyProps(archive)),
        },
        "diagnostics": [[row.code, row.message] for row in document.diagnostics],
        "configuration_names": [row.name for row in document.configurations],
        "tree": feature_rows(document),
        "parameters": [
            {
                "name": row.name,
                "owner": row.owner_id,
                "value_mm": row.value.value,
                "role": str(row.role),
                "native_role": row.attributes.get("native_role"),
                "native_value": row.attributes.get("native_value"),
                "archive_owned": "typed_archive_owner" in row.attributes,
            }
            for row in document.parameters
        ],
        "sketches": [
            {
                "entities": len(row.entities),
                "relations": len(row.constraints),
                "profiles": [len(profile) for profile in row.closed_profile_entity_ids],
                "support": row.support_plane_id,
                "typed_line_loop": row.attributes.get("typed_line_loop", False),
            }
            for row in document.sketches
        ],
        "body": None if part is None else {
            "name": part.name,
            "volume_mm3": part.topology.volume,
            "solids": part.topology.solid_count,
            "faces": part.topology.face_count,
            "edges": part.topology.edge_count,
            "vertices": part.topology.vertex_count,
            "active_payload": part.attributes.get("parasolid_active_payload_id"),
        },
        "payloads": [{"role": str(row.role), "id": row.id} for row in document.brep_payloads],
    }


def compare_one(authored_root, output, acquired, case, authored_name):
    measured_root = ROOT / "re/solidworks/measurements/2026/EncoderRoundTrip"
    native_name = authored_name + ".SLDPRT"
    raw = (authored_root / native_name).read_bytes()
    observed = acquired["authored"][native_name]
    if digest(raw) != observed["sha256"]:
        raise ValueError(f"{native_name} differs from its native authoring record")
    envelope = json.loads((measured_root / (case + ".json")).read_bytes())
    request = CadDocument.from_json((measured_root / "Requests" / (case + ".json")).read_text(encoding="utf-8"))
    locator = rf"C:\KitEncoderRoundTrip\{request.metadata['name']}.SLDPRT"
    cold = construct(request, locator, envelope["written_at"]).BytesValue
    expected = envelope["receipt"]["builds"][0]["candidate_sha256"]
    if digest(cold) != expected:
        raise ValueError(f"{case} cold control differs from its native measurement")
    return {
        "vendor": inspected(raw, output / "Vendor" / (case + ".json")),
        "cold": inspected(cold, output / "Cold" / (case + ".json")),
        "vendor_oracle_tree": [[row["name"], row["type"]] for row in observed["body"]["tree"]],
    }


def main():
    parser = ArgumentParser(description="Inventory ordinary vendor bosses and their exact measured cold controls")
    parser.add_argument("--authored-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    record = (args.authored_root / "Record.json").read_bytes()
    acquired = json.loads(record)
    if acquired["passed"] is not True:
        raise ValueError("the vendor authoring record did not pass")
    args.output.mkdir(parents=True, exist_ok=False)
    for label in ("Vendor", "Cold"):
        (args.output / label).mkdir()
    cases = {
        group + state: compare_one(args.authored_root, args.output, acquired, group + state, group + source)
        for group in ("Baseline", "HeldOut")
        for state, source in (("Reconstruction", "Source"), ("Edited", "EditedControl"))
    }
    report = {
        "source_author_record_sha256": digest(record),
        "oracle": {key: acquired["oracle_identity"][key] for key in ("build", "sha256")},
        "python": sys.version.split()[0],
        "zlib": ZLIB_RUNTIME_VERSION,
        "cases": cases,
    }
    with (args.output / "Inventory.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


if __name__ == "__main__":
    main()
