from __future__ import annotations

import argparse
import dis
from hashlib import sha256
import json
from pathlib import Path
from xml.etree.ElementTree import fromstring

from Classes import registry
from RoundTrip import PLANS, stream_roundtrip
from Streams import load_rooted
from convert.adapters.solidworks.Container.Container import SldprtArchive


SCHEMA = "kit.sw2026.part-property-source.v1"
ORACLE = "3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
PROPERTY_NAMES = {"title": "title", "subject": "subject", "author": "creator",
                  "keywords": "keywords", "comments": "description"}
DC = "http://purl.org/dc/elements/1.1/"
TYPES = "http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"
CUSTOM = "http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"
CONFIG = "http://www.solidworks.com/config-properties"
MANAGER = "Contents/CusProps"


def require(value, message):
    if not value:
        raise ValueError(message)


def checked(path, expected):
    data = path.read_bytes()
    require(sha256(data).hexdigest() == expected, f"frozen input changed: {path.name}")
    return data


def read_record(path, reference):
    payload = checked(path, reference["record_sha256"])
    result = json.loads(payload)
    if path.parent.name.startswith("Control"):
        features = result.get("features", ())
        require(result["opened"] and result["rebuilt"] and result["bodies"] > 0
                and result["open_errors"] == result["open_warnings"] == result["whats_wrong"] == 0
                and result["mass"]["volume"] > 0 and features
                and all(row.get("error") == 0 and row.get("warning") is False for row in features)
                and not any(result.get(field) for field in ("exception", "controller_diagnostics", "dialogs")),
                "native source control did not pass")
    else:
        require(result["passed"] and not result.get("first_failure")
                and not result.get("cleanup_errors"), f"native phase did not pass: {path.parent.name}")
    checks = result.get("checks", [])
    require(all(row["passed"] for row in checks), "numeric comparison failed")
    return len(checks)


def read_text_xml(payload, wanted, configured):
    root = fromstring(payload)
    namespace, root_name = (CONFIG, "ConfigProperties") if configured else (CUSTOM, "Properties")
    require(root.tag == f"{{{namespace}}}{root_name}" and len(root) == 2
            and all(section.tag == "propertySection" for section in root), "property bag vocabulary changed")
    scope, user = root
    require(scope.get("name") == "DocumentSummaryInformation" and user.get("name") == "UserDefinedProperties",
            "property sections lost their actual scope")
    dictionary, entries, reserved = [], [], []
    for row in user:
        pid = int(row.get("pid"))
        name = row.get("name")
        if row.tag == "propertyNameDictionaryElement":
            dictionary.append((name, pid))
        elif name:
            require(row.tag == "property" and 1 <= len(row) <= 2 and row[0].tag == f"{{{TYPES}}}lpstr"
                    and row.get("IsEquation") == "False", "non-text or evaluated-expression custom property")
            value = row[0].text
            results = []
            if len(row) == 2:
                require(row[1].tag == "FPVals" and len(row[1]) == 1 and row[1][0].tag == f"{{{TYPES}}}lpstr",
                        "expected one text evaluation in this measured property profile")
                results = [row[1][0].text]
                require(results == [value], "evaluated custom text differs from the authored value")
            entries.append({"name": name, "pid": pid, "type_id": int(row.get("TypeID")), "evaluated_values": len(results)})
            require(wanted[name] == value, "persisted custom text differs from the neutral API request")
        else:
            require(row.tag == "property" and len(row) == 1, "reserved property row is malformed")
            reserved.append([pid, row[0].tag.split("}")[-1], row[0].text])
    require([item["name"] for item in entries] == list(wanted)
            and [item["pid"] for item in entries] == list(range(3, 3 + len(wanted)))
            and dictionary == [("", 0), *((x["name"], x["pid"]) for x in sorted(entries, key=lambda row: row["name"]))],
            "property ids or dictionary no longer follow the observed source order")
    return {"namespace": namespace, "entries": entries, "reserved": reserved, "dictionary": dictionary,
            "summary_ids": [int(row.get("pid")) for row in scope]}


def read_source(path, case, reg, expected):
    data = checked(path, expected)
    archive = SldprtArchive.FromBytes(data)
    core = fromstring(archive.Require("docProps/core.xml"))
    require(all(core.findtext(f"{{{DC}}}{PROPERTY_NAMES[name]}") == text for name, text in case["summary"].items()),
            "ordinary file summary text lost its exact document property")
    xml = {"summary_fields": [node.tag.split("}")[-1] for node in core]}
    streams = {"core": "docProps/core.xml", "document": "docProps/custom.xml",
               "configured": "docProps/Config-0-Properties.xml", "advanced_manager": MANAGER}
    for owner in ("document", "configured"):
        xml[owner] = read_text_xml(archive.Require(streams[owner]), case[owner], owner == "configured")
    report = stream_roundtrip(archive, MANAGER, reg, {**PLANS, **reg.plans})
    require(report["passed"] and report["roots"] == 1 and report["tail"] == 0,
            "typed property manager must round-trip completely")
    parsed, _ = load_rooted(archive.Require(MANAGER), reg, 1, 19000)
    root, = parsed.roots
    advanced = root["f20"]
    if advanced:
        row, = advanced
        file = row["o"]["f08"]
        require(row["key"] == 0 and file.cls == "moFilePropContainer_c", "advanced file section lost its owner")
        for label, field in (("document", "f08"), ("configured", "f10")):
            slots = file[field]["items"]
            tables = slots[0]["o"]["items"]
            require(len(slots) == 1 and len(tables) == len(case[label]), "advanced property count differs")
            for value, (name, text) in zip(tables, case[label].items(), strict=True):
                item = value["o"]
                embedded, = item["f10"]["items"]
                require(item["f58"] == name and item["f60"] == item["f70"] == embedded["o"]["f08"] == text
                        and embedded["o"].cls == "moCusPropStringElem_c",
                        "advanced property no longer names the independently evaluated text")
    return {"save_sha256": expected, "xml": xml, "archive_streams": {
                key: {"bytes": len(archive.Require(name)), "sha256": sha256(archive.Require(name)).hexdigest()}
                for key, name in streams.items()},
            "advanced_manager": {"map_base": report["map_base"], "terminal_map": report["map_count"],
                                 "f08": root["f08"], "f0c": root["f0c"], "container_count": root["n20"],
                                 "f54": root["f54"], "byte_exact": True}}


def audit(root, packet_sha, result_sha, host_sha):
    packet = json.loads(checked(root / "Packet.json", packet_sha))
    result_root = root / "Inspection"
    native = json.loads(checked(result_root / "Result.json", result_sha))
    host = json.loads(checked(root / "Host02.json", host_sha))
    require(packet["schema"] == native["schema"] == SCHEMA and packet["oracle_sha256"] == ORACLE
            and native["packet_sha256"] == packet_sha and native["passed"] and native["controls_healthy"]
            and native["distinct_processes"] == 6 and native["heldout_inputs_read"] == 0
            and host["supervisor_exit_code"] == host["transport_returncode"] == 0,
            "invalid measured source packet or run")
    for name, digest in packet["tools_sha256"].items():
        checked(root / "Tools" / name, digest)
    checked(root / "Control.SLDPRT", packet["control_sha256"])
    reg = registry()
    cases, phases = {}, []
    distinct = set()
    ordered = ["ControlBefore", *(case["name"] + suffix for case in packet["cases"] for suffix in ("Author", "Reopen")), "ControlAfter"]
    for role in ordered:
        row = native["phases"][role]
        identity = row["oracle_identity"]
        process = identity["process_creation_filetime"]
        require(row["passed"] and identity["version_matches"] and identity["sha256"] == ORACLE
                and process not in distinct, "native process or oracle differs")
        distinct.add(process)
        count = read_record(result_root / role / "Record.json", row)
        phases.append({"phase": role, "record_sha256": row["record_sha256"], "numeric_checks": count,
                       "process_creation_filetime": process})
    for case in packet["cases"]:
        checked(root / case["input"], case["input_sha256"])
        role = case["name"] + "Author"
        row = native["phases"][role]
        target = result_root / role / row["saved_name"]
        cases[case["name"]] = read_source(target, case, reg, row["saved_sha256"])
    return {"schema": SCHEMA, "packet_sha256": packet_sha, "native_result_sha256": result_sha, "host_sha256": host_sha,
            "oracle_sha256": ORACLE, "native_version": "34.5.2.0604", "distinct_processes": len(distinct),
            "controls_healthy": True, "source_observed": True, "heldout_inputs_read": 0, "writer_outputs": 0,
            "phases": phases, "cases": cases, "passed": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--packet-sha256", required=True)
    parser.add_argument("--result-sha256", required=True)
    parser.add_argument("--host-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    data = audit(options.root, options.packet_sha256, options.result_sha256, options.host_sha256)
    with options.output.open("x", encoding="utf-8") as output:
        json.dump(data, output, indent=2, ensure_ascii=False, allow_nan=False)
        output.write("\n")
    print(json.dumps({"passed": True, "sha256": sha256(options.output.read_bytes()).hexdigest(),
                      "processes": data["distinct_processes"], "cases": len(data["cases"]),
                      "numeric_checks": sum(row["numeric_checks"] for row in data["phases"])}))


if __name__ == "__main__":
    main()
