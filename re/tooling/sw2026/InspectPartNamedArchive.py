from argparse import ArgumentParser
from hashlib import sha256
from json import dumps, loads
from math import isclose
from pathlib import Path

from convert import open_document
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KEYWORDS_STREAM
from convert.adapters.solidworks.Core.Native import ParseKeywords
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from para.Partition import frame_payloads, read_partition, write_payloads


def read_locked(path, checksum):
    data = path.read_bytes()
    if sha256(data).hexdigest() != checksum:
        raise ValueError(f"input hash differs for {path.name}")
    return data


def get_fields(value, path):
    for key in path:
        if hasattr(value, "FieldsValue"):
            value = value.FieldsValue
        value = value[key]
    return value


def read_parameters(roots):
    locations = (
        (17, "pd_f80", "dims", "val_g2", 0, "d", "f28"),
        (17, "pd_f80", "dims", "val_g2", 1, "d", "f28"),
        (18, "f818", "f18", "f850", 0, "o", "ff0", "f28"),
    )
    result = []
    for path in locations:
        node = get_fields(roots, path)
        name = node.FieldsValue["f18"]
        if (
            node.ClassValue.NameValue != "moLengthParameter_c"
            or name.ClassValue.NameValue != "moNodeName_c"
            or node.FieldsValue["f08"] != -1
            or node.FieldsValue["f48"] is not None
        ):
            raise ValueError("driving length has an unexpected owner or alternate state")
        result.append(
            {
                "owner": ".".join(map(str, path)),
                "name": name.FieldsValue["f08"],
                "length_m": node.FieldsValue["f58"],
            }
        )
    return result


def read_body_name(partition):
    nodes = {node.index: node for node in partition.nodes}
    characters = tuple(node for node in partition.nodes if node.kind == 84)
    if not characters:
        return None
    (value,) = characters
    (attribute,) = tuple(
        node for node in partition.nodes if node.kind == 81 and value.index in node.fields["fields"]
    )
    definition = nodes[attribute.fields["definition"]]
    identity = nodes[definition.fields["identifier"]]
    owner = nodes[attribute.fields["owner"]]
    if (
        (owner.kind, definition.kind, identity.kind) != (12, 80, 79)
        or identity.fields["string"] != "SDL/TYSA_NAME"
        or definition.fields["type_id"] != 8017
        or definition.fields["fields"] != (3,)
        or attribute.fields["fields"] != (value.index,)
    ):
        raise ValueError("unexpected explicit body name graph")
    deletion_marks = [
        entry.mark.fields["id"]
        for entry in partition.history
        if entry.rollback and (value.index, 84) in entry.rollback.deleted
    ]
    if len(deletion_marks) != 1:
        raise ValueError("body name value is not owned by the active rollback")
    return {
        "body_node_kind": owner.kind,
        "definition": identity.fields["string"],
        "definition_type_id": definition.fields["type_id"],
        "field_types": definition.fields["fields"],
        "value_kind": value.kind,
        "value": value.fields["values"],
        "rollback_mark_ids": deletion_marks,
    }


def read_keyword_names(archive, expected):
    data = archive.require(KEYWORDS_STREAM)
    configurations, features = ParseKeywords(data)
    owners = {qualified.split("@", 1)[1] for qualified in expected}
    rows = {}
    for feature in features:
        if feature.name not in owners:
            continue
        if feature.name in rows:
            raise ValueError("keyword feature ownership is ambiguous")
        rows[feature.name] = {dimension.name: dimension.value_mm for dimension in feature.dimensions}
    actual = {f"{name}@{owner}": value for owner, dims in rows.items() for name, value in dims.items()}
    if len(configurations) != 1 or actual.keys() != expected.keys():
        raise ValueError("keyword dimensions differ from their actual native owners")
    if any(not isclose(value, expected[name] * 1000, rel_tol=1e-12) for name, value in actual.items()):
        raise ValueError("keyword dimension length differs from the native driver")
    return {"stream_sha256": sha256(data).hexdigest(), "stream_bytes": len(data), "dimensions_mm": actual}


def read_public_names(path, expected):
    document = open_document(path, strict=True, include_brep=True, include_tessellation=False)
    owners = {feature.id: feature.name for feature in document.feature_timeline}
    actual = {
        name: parameter.value.value
        for parameter in document.parameters
        if (name := f"{parameter.name}@{owners.get(parameter.owner_id)}") in expected["drivers_m"]
        and parameter.role.value == "driving"
        and parameter.value.unit == "mm"
    }
    if actual.keys() != expected["drivers_m"].keys():
        raise ValueError("strict SDK reading did not preserve every named driving parameter")
    if any(not isclose(value, expected["drivers_m"][name] * 1000, rel_tol=1e-12) for name, value in actual.items()):
        raise ValueError("strict SDK parameter length differs from the native driver")
    if len(document.bodies) != 1 or document.brep is None or len(document.brep.bodies) != 1:
        raise ValueError("strict SDK result lacks the single measured native body")
    body, = document.bodies
    return {
        "driver_dimensions_mm": actual,
        "design_body_label": body.name,
        "design_body_final_feature": owners.get(body.final_feature_id),
        "body_label_matches_native": body.name == expected["body_name"],
        "diagnostics": [diagnostic.code for diagnostic in document.diagnostics],
    }


def inspect(path, checksum, expected):
    data = read_locked(path, checksum)
    archive = SldprtArchive.from_bytes(data, path)
    stream = archive.require("Contents/Config-0-Partition")
    partition = read_partition(stream)
    if frame_payloads(write_payloads(partition)) != stream:
        raise ValueError("typed partition framing differs")
    body_name = read_body_name(partition)
    if body_name is not None and body_name["value"] != expected["body_name"]:
        raise ValueError("explicit body name differs from the native observer")
    link = ReadNativeLink(archive, 0)
    drivers = read_parameters(link.ResolvedValue.RootsValue)
    observed = tuple(expected["drivers_m"].items())
    driver_entries = tuple((name.split("@", 1)[0], value) for name, value in observed)
    if tuple((row["name"], row["length_m"]) for row in drivers) != driver_entries:
        raise ValueError("archive parameter names or independent lengths differ")
    return {
        "file_sha256": checksum,
        "partition_sha256": sha256(stream).hexdigest(),
        "partition_bytes": len(stream),
        "partition_nodes": len(partition.nodes),
        "partition_round_trip_exact": True,
        "actual_native_body_label": expected["body_name"],
        "body_name_attribute": body_name,
        "driver_owners": drivers,
        "keywords": read_keyword_names(archive, expected["drivers_m"]),
        "strict_sdk": read_public_names(path, expected),
    }


def main():
    parser = ArgumentParser()
    parser.add_argument("packet", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--native-sha256", required=True)
    args = parser.parse_args()
    read_locked(args.packet / "Packet.json", args.packet_sha256)
    root = args.packet / "Inspection"
    native_result = loads(read_locked(root / "Result.json", args.native_sha256))
    if not native_result["passed"] or not native_result["controls_healthy"]:
        raise ValueError("native source comparison or controls failed")
    records = []
    for case in native_result["cases"]:
        author = case["author"]
        fresh = case["reopen"]
        files = root / case["name"] / "Author"
        baseline = inspect(files / "Baseline.SLDPRT", author["baseline_sha256"], author["baseline"])
        renamed = inspect(files / "Renamed.SLDPRT", author["renamed_sha256"], author["renamed"])
        if baseline["body_name_attribute"] is not None or renamed["body_name_attribute"] is None:
            raise ValueError("baseline and explicit names do not have distinct ownership")
        if (
            fresh["reopened"]["drivers_m"] != author["renamed"]["drivers_m"]
            or fresh["reopened"]["body_name"] != author["renamed"]["body_name"]
            or fresh["edited"]["body_name"] != author["renamed"]["body_name"]
        ):
            raise ValueError("native reopen did not preserve measured names")
        records.append(
            {
                "case": case["name"],
                "baseline": baseline,
                "renamed": renamed,
                "fresh_body_label": fresh["reopened"]["body_name"],
                "fresh_parameters_m": fresh["reopened"]["drivers_m"],
                "fresh_edited_parameters_m": fresh["edited"]["drivers_m"],
                "author_record_sha256": author["record_sha256"],
                "reopen_record_sha256": fresh["record_sha256"],
            }
        )
    receipt = {
        "schema": "kit.sw2026.part-name-archive-disclosure.v2",
        "packet_sha256": args.packet_sha256,
        "native_result_sha256": args.native_sha256,
        "native_processes": native_result["distinct_processes"],
        "controls_healthy": True,
        "oracle_file_version": native_result["controls"][0]["oracle_identity"]["file_version"],
        "oracle_sha256": native_result["controls"][0]["oracle_identity"]["sha256"],
        "partition_round_trips": 2 * len(records),
        "cases": records,
        "heldout_inputs_read": 0,
        "writer_output_count": 0,
    }
    with args.output.open("x", encoding="utf-8", newline="\n") as output:
        output.write(dumps(receipt, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
