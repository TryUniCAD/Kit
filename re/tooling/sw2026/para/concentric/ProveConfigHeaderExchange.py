from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from struct import Struct, unpack_from
import subprocess
import sys
from uuid import UUID


HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))

from ProveAssemblyMateDescriptor import cases, require_refusal
from ProveD01PropertyTransport import CASE_MANIFESTS, REPO, checked, proof_guard, require, wire
from D01RevisionIntent import ordered_occurrences
from InspectPartEnvironmentSource import Image
from PrepareGeneratedConcentric import windows_path
from ProveSdkConcPlan import preload
from ProveSdkCylParent import CASES, create, parent
from ConfigHeaderExchangeModel import (
    CONFIG_FIELDS, CONFIG_HEADER_STREAM, MODEL_EXCHANGE_STREAM, config_header_cell, encode_config_header,
    project_active_config, project_config_header, read_config_header, read_model_exchange_link, read_uuid_key,
)
from ExchangeMessagePack import encode_config_atom, read_exchange_map

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.CmgrHeader.ReadMgrHeader import ReadMgrHeader
from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHeader import WriteMgrHeader
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.ReadOccName import ReadOccName
from convert.adapters.solidworks.Archive.Construction.Metadata.ManagerHeader.MakeMgrEntry import MakeMgrEntry
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, ReadNodeName
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange.serialization.Deserialize import FromData


BASE = "2e3c2ab7c83ae5f6632dbc0bf64482f7546d8bab"
MODULE = "5f743916826fd26a25c8d4792ada785d414d1c718c32495e481b1c5dc512ac48"
PRIOR = "676fb1e7e56e929d880a7de1471acf7cb456b70f9fec862f00961fc597736c51"
RENAMED = "481a13c6f3c068d6df56521b7b0bb31c63f13404dbc0e2f469b0ca6d4034c83c"
HEADER = "Contents/CMgrHdr2"
MANAGER = "Contents/CMgr"
PAGE_SIZE = 4096
CELL = Struct(">IIQHQ")
VERSION = 19000


def digest(value):
    return sha256(value).hexdigest()


def observed_cells(data):
    require(len(data) == 3 * PAGE_SIZE and data.startswith(b"unqlite"),
            "only the disclosed three-page transport can be inspected")
    page = data[-PAGE_SIZE:]
    at, _, link = unpack_from(">HHQ", page)
    require(link == 0, "unexpected bucket overflow")
    rows = []
    visited = set()
    while at:
        require(at >= 12 and at + CELL.size < len(page) and at not in visited, "foreign observed live cell")
        visited.add(at)
        _, key_size, value_size, next_at, overflow = CELL.unpack_from(page, at)
        start = at + CELL.size
        middle = start + key_size
        end = middle + value_size
        require(overflow == 0 and key_size > 0 and value_size > 0 and end <= len(page),
                "unexpected disclosed cell lengths")
        rows.append((page[start:middle], page[middle:end]))
        at = next_at
    return tuple(reversed(rows))


def static_evidence(path):
    image = Image(path, MODULE)
    keys = ((0x31A0FDC8, "configHeaderfamilyMemberID"), (0x31A0FDE4, "class"), (0x31A0FDEC, "name"),
            (0x31A0FDF4, "id"), (0x31A0FDF8, "_3dExpType"), (0x31A0FE08, "repParent"),
            (0x31A0FEF0, "overriddenReferenceIDs"))
    for address, key in keys:
        encoded = key.encode("ascii") + b"\0"
        require(image.read(address, address + len(encoded)) == encoded, "native MessagePack vocabulary differs")
    imported = image.imports()["0x31a0e720"]
    require(imported == {"module": "sldutu.dll", "name": "?GetSWGUID@@YAPEADXZ"}, "native UUID creator differs")
    ranges = {"config_key": (0x319F8880, 0x319F88A5), "manager_key": (0x319F88B0, 0x319F88D8),
              "family_type": (0x319FA47C, 0x319FA504), "empty_override_gate": (0x319FA6D6, 0x319FA6E3),
              "manager_row_gate": (0x319F9337, 0x319F9356)}
    return {"sha256": MODULE, "key_vocabulary": {key: hex(address) for address, key in keys},
            "uuid_import": imported,
            "native_windows": {name: {"start": hex(start), "end_exclusive": hex(end),
                                       "sha256": digest(image.read(start, end))}
                               for name, (start, end) in ranges.items()}}


def inspect_source(path, pin):
    archive = SldprtArchive.from_bytes(checked(path, pin))
    binary_manager = archive.require(MANAGER)
    directory_data = archive.require(HEADER)
    directory = ReadMgrHeader(directory_data, VERSION).RootValue
    manager = ReadCmgrMut(binary_manager, VERSION).RootValue
    require(WriteMgrHeader(directory, VERSION)[0] == directory_data and WriteCmgrMut(manager, VERSION) == binary_manager,
            "actual lightweight or model configuration manager fails typed replay")
    row, = directory.FieldsValue["f08"]["items"]
    value = project_config_header(row["o"], project_active_config(manager))
    source_config = archive.require(CONFIG_HEADER_STREAM)
    source_model = archive.require(MODEL_EXCHANGE_STREAM)
    (key, payload), = observed_cells(source_config)
    decoded, identity = read_config_header(key, payload)
    require(decoded == value and len(payload) == 92 and encode_config_header(value) == payload,
            "source exchange map differs from its independently projected configuration")
    model_cells = observed_cells(source_model)
    manager_identity, overrides = read_model_exchange_link(model_cells, manager, value)
    model_keys = tuple(raw for raw, _ in model_cells)
    model_uuid_keys = tuple(read_uuid_key(raw) for raw in model_keys if raw != b"TOC")
    require(len(model_cells) == 8 and len(set(model_uuid_keys)) == 7
            and identity not in model_uuid_keys and manager_identity in model_uuid_keys,
            "expected separate model and configuration UUID namespaces")
    root = ReadNativeLink(archive, 0).ConfigValue.RootValue
    refs = ordered_occurrences(root) if "f68" in root.FieldsValue else ()
    require(len(refs) == FieldInt(root.FieldsValue, "f1560"), "actual occurrence list does not match its owner count")
    custom = tuple(FieldInt(ref.FieldsValue, "f08") for ref in refs
                   if ReadOccName(ReadNodeName(ref))[0] != ReadFileKey(ref.FieldsValue["f3b0"])[0])
    return {"source_sha256": pin, "header_store_sha256": digest(source_config),
            "header_value_sha256": digest(payload), "header_key_sha256": digest(key), "header_value_bytes": len(payload),
            "model_store_sha256": digest(source_model), "model_cells": len(model_cells),
            "model_manager_key_sha256": digest(str(manager_identity).encode("ascii")), "configuration_id": value.configuration_id,
            "configuration_name": value.name, "model_toc_join_verified": True,
            "model_override_ids": overrides, "header_override_records": 0, "separate_uuid_ownership": True,
            "occurrence_count": len(refs), "custom_occurrence_ids": custom}


def source_cases(disclosures, prior):
    yield from cases(disclosures, prior)
    root = REPO / "re/solidworks/v2026/corpus/assembly-synchronized"
    manifest, _ = CASE_MANIFESTS[root.name]
    name = "A12SyncedEmpty.SLDASM"
    row, = (row for row in json.loads(checked(root / "Manifest.json", manifest))["records"]
            if row.get("file") == name)
    yield name, root / name, row["sha256"]
    yield ("renamed_native", disclosures / "ConcentricNameBaseSetterRetry01/NativePacket02/Native/Source"
           / "CustomNameOwnershipControl.SLDASM", RENAMED)


def authored_configuration(document, name):
    graph = document.assembly
    definitions = tuple(replace(row, configuration_name=name) if row.id == graph.root_definition_id else row
                        for row in graph.definitions)
    return replace(document, configurations=(replace(document.configurations[0], name=name),),
                   assembly=replace(graph, definitions=definitions))


def scoped_map(pairs):
    return bytes((0x80 + len(pairs),)) + b"".join(
        encode_config_atom(key) + (value if type(value) is bytes else encode_config_atom(value))
        for key, value in pairs
    )


def negatives(actual, light, model, key, payload):
    manager = actual.ManagerValue
    config = actual.CurrentConfig
    wrong = ArchiveNode(light.ClassValue, dict(light.FieldsValue, f34=7))
    id_crossed = ArchiveNode(light.ClassValue, dict(light.FieldsValue, f30=1))
    fields = read_exchange_map(payload)
    bad_order = scoped_map(tuple(reversed(fields.pairs)))
    fake_family = scoped_map(tuple((k, -1 if k == "configHeaderfamilyMemberID" else v) for k, v in fields.pairs))
    fake_toc = scoped_map((("class", "object-map"), ("model", scoped_map((
        ("class", "moAssembly_c"), ("configid", model.configuration_id), ("configname", model.name + " changed"))))))
    true_toc = scoped_map((("class", "object-map"), ("model", scoped_map((
        ("class", "moAssembly_c"), ("configid", model.configuration_id), ("configname", model.name))))))
    unproved_override = scoped_map((("class", "moConfigurationMgr_c"), ("id", manager.FieldsValue["f08"]),
                                   ("overriddenReferenceIDs", b"\x91\x18")))
    return {
        "foreign_lightweight_id": require_refusal(lambda: project_config_header(id_crossed, config), "ordinary active"),
        "unqualified_parent": require_refusal(lambda: project_config_header(wrong, config), "ordinary active"),
        "wrong_map_order": require_refusal(lambda: read_config_header(key, bad_order), "fields or order"),
        "unsupported_family_member": require_refusal(lambda: read_config_header(key, fake_family), "family or representation"),
        "noncanonical_uuid": require_refusal(lambda: read_config_header(key.upper(), payload), "canonical version-four"),
        "trailing_map_bytes": require_refusal(lambda: read_config_header(key, payload + b"\0"), "one complete"),
        "foreign_model_configuration": require_refusal(lambda: read_model_exchange_link(
            ((b"TOC", fake_toc),), manager, model), "different assembly configuration"),
        "unproved_override_state": require_refusal(lambda: read_model_exchange_link(
            ((b"TOC", true_toc), (key, unproved_override)), manager, model), "nonempty persisted reference overrides"),
    }


def worker(request):
    require(set(request) == {"document", "ambient", "destination", "epoch", "new_record_ids"},
            "exchange worker accepts only authored neutral intent and fresh allocation")
    ordinary = FromData(request["document"])
    alternate = authored_configuration(ordinary, "Adjusted mechanism configuration 検")
    identities = tuple(UUID(text) for text in request["new_record_ids"])
    require(len(set(identities)) == len(identities) == 2, "requires two independent configuration identities")
    for document in (ordinary, alternate):
        preload(document)
    audit = proof_guard()
    result = {}
    for label, document, identity in zip(("normal", "varied_name"), (ordinary, alternate), identities, strict=True):
        args = (document, None, request["ambient"], request["destination"], request["epoch"], None)
        bundle = parent(create("persistence", args), None, None)
        actual = bundle.StateValue
        config = project_active_config(actual.ManagerValue)
        light = MakeMgrEntry(config, actual.RootValue)
        value = project_config_header(light, config)
        key, payload = config_header_cell(value, identity)
        require(read_config_header(key, payload) == (value, identity)
                and value.name == document.configurations[0].name, "new cell loses the authored configuration owner")
        result[label] = {"parent_sha256": digest(bundle.BytesValue), "child_sha256": digest(bundle.ChildValue.BytesValue),
                         "value_sha256": digest(payload), "key_sha256": digest(key), "value_bytes": len(payload),
                         "configuration_name": value.name, "id": value.configuration_id}
    result["refusals"] = negatives(actual, light, value, key, payload)
    require(not audit and result["normal"]["child_sha256"] == result["varied_name"]["child_sha256"]
            and result["normal"]["value_bytes"] < result["varied_name"]["value_bytes"],
            "exchange construction accessed external inputs or changed its unrelated child")
    return {"model_only": result, "runtime_access_attempts": len(audit)}


def main():
    parser = ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--worker", action="store_true")
    mode.add_argument("--disclosures", type=Path)
    parser.add_argument("--archive-image", type=Path)
    options = parser.parse_args()
    if options.worker:
        sys.stdout.buffer.write(wire(worker(json.load(sys.stdin))))
        return
    require(options.archive_image is not None, "requires the exact disclosed sldarchive module")
    authority = static_evidence(options.archive_image)
    prior = json.loads(checked(REPO / "re/solidworks/measurements/2026/ConcentricD01PropertyTransport01.json", PRIOR))
    sources = {label: inspect_source(path, pin) for label, path, pin in source_cases(options.disclosures, prior)}
    require(len({row["header_key_sha256"] for row in sources.values()}) == len(sources) == 12
            and sources["renamed_native"]["custom_occurrence_ids"] == (24, 25)
            and sources["renamed_native"]["model_override_ids"] == ()
            and all(sources[slot + "/Source"]["model_manager_key_sha256"] ==
                    sources[slot + "/Edited"]["model_manager_key_sha256"] for slot in ("D01", "D02", "D03")),
            "native owner identity or ordinary custom-name contrast differs")
    packet, packet_pin = CASES["persistence"]
    folder = options.disclosures / packet
    trial = json.loads(checked(folder / "Trial.json", packet_pin))

    def evidence(role):
        key = "Evidence/" + role + ".json"
        return json.loads(checked(folder / key, trial["files_sha256"][key]))

    request = wire({"document": evidence("Neutral"), "ambient": evidence("Ambient"),
                    "destination": windows_path(folder / "Working" / trial["working_names"]["parent"]),
                    "epoch": evidence("Build")["written_at"],
                    "new_record_ids": ("6dce4dde-a992-43a9-bbc1-b58d6bd22ffa", "88de9e9c-48fa-4d6d-b6b1-b2a389c97d1b")})
    command = (sys.executable, "-I", "-B", str(HERE), "--worker")
    first, second = (subprocess.run(command, input=request, capture_output=True, timeout=180) for _ in range(2))
    require(first.returncode == second.returncode == 0 and first.stdout == second.stdout,
            (first.stderr + second.stderr).decode() or "independent exchange workers differ")
    generated = json.loads(first.stdout)
    require(all(generated["model_only"]["normal"][role + "_sha256"] == trial["generated_sha256"][role]
                for role in ("parent", "child")), "previous complete persistence pair differs")
    print(json.dumps({"schema": "kit.sw2026.config-header-exchange.v1", "base": BASE, "native_authority": authority,
                      "sources": sources, "source_owner_fields": CONFIG_FIELDS, "guarded_workers": 2,
                      "neutral_request_sha256": digest(request), "generated": generated,
                      "native_runs": 0, "heldout_accesses": 0,
                      "tool_sha256": {name: digest(HERE.with_name(name).read_bytes())
                                      for name in ("ConfigHeaderExchangeModel.py", "ExchangeMessagePack.py", HERE.name)}},
                     indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
