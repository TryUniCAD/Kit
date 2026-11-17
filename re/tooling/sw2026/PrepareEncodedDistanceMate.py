from __future__ import annotations

import argparse
import json
from pathlib import Path, PureWindowsPath
from shutil import copyfile
import subprocess
import sys

from AuthorCurves import digest, require, write_json
from InspectEncodedDistanceMate import BASE_PACKET, BASE_RESULT, ORACLE_FOLDER, SCHEMA, SCRIPT
from InspectGeneratedDistanceMate import SOURCE_ARTIFACTS, checked, pair_paths


HOST_SHA = "e1042c5bf66eaebdb11f46075daf7766c41c2053fa68ddafadf147c3a4724d79"
HEADERS = ("Header2", "Contents/Config-0-ModelHeader")
CONFIG = "Contents/Config-0"


def definitions(data, rules):
    from Core import DOCUMENT_VERSION_2026
    from Streams import load_rooted, store_rooted

    document, _ = load_rooted(data, rules, 1, DOCUMENT_VERSION_2026)
    require(not document.tail and store_rooted(document, rules, DOCUMENT_VERSION_2026) == data, "header file definitions did not round trip")
    header, = document.roots
    child_list = header["f30"]
    return {
        "self": file_path(header["f38"]["shared"]),
        "children": [file_path(row["o"]["shared"]) for row in child_list["items"]] if child_list else [],
    }


def file_path(fields):
    return fields["h18"]["f08"]


def read_encoded_paths(paths):
    from Classes import registry
    from Core import DOCUMENT_VERSION_2026
    from defs.ConfigPart import load_config, store_config_state
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    parent, child = (SldprtArchive.from_bytes(path.read_bytes()) for path in paths)
    rules = registry()
    parent_headers, child_headers = (
        {stream: definitions(archive.require(stream), rules) for stream in HEADERS} for archive in (parent, child)
    )
    payload = parent.require(CONFIG)
    config, _ = load_config(payload, rules, DOCUMENT_VERSION_2026, archive=parent, name=CONFIG)
    require(not config.tail and store_config_state(config, rules, DOCUMENT_VERSION_2026)[0] == payload,
            "occurrence file definitions did not round trip")
    assembly, = config.roots
    occurrences = [
        {
            "name": row["o"]["f18"]["f08"], "child": file_path(row["o"]["f3b0"]["shared"]),
            "parent_backlink": file_path(row["o"]["f4f8"]["f10"]),
        }
        for row in assembly["f68"]["list"]["items"]
    ]
    return {"parent_headers": parent_headers, "child_headers": child_headers, "occurrence_refs": occurrences}


def prove_path_pair(source, packet):
    generated = packet["generated"]
    paths = pair_paths(source / "FrozenGenerated", generated["case"], generated["files"])
    request = json.loads(checked(source / "Request.json", generated["source_artifact_sha256"]["Request.json"], owner=source).read_bytes())
    encoded = [request["bundle"][role]["output"]["path_name"] for role in ("assembly", "child")]
    parent, child = encoded
    require(all(PureWindowsPath(name) == ORACLE_FOLDER / path.name for path, name in zip(paths, encoded, strict=True)),
            "candidate was authored for different output paths")
    observed = read_encoded_paths(paths)
    require(observed == {
        "parent_headers": {key: {"self": parent, "children": [child]} for key in HEADERS},
        "child_headers": {key: {"self": child, "children": []} for key in HEADERS},
        "occurrence_refs": [{"name": name, "child": child, "parent_backlink": parent} for name in generated["case"]["occurrence_names"]],
    }, "decoded file definitions differ from the authored request")
    return paths, dict(zip((path.name for path in paths), encoded, strict=True)), observed


def prepare(source, output):
    require(source != output and source.parent == output.parent and not output.exists() and not output.is_symlink(),
            "choose an unused sibling of the first private distance trial")
    original = checked(source / "Trial.json", BASE_PACKET, owner=source)
    packet = json.loads(original.read_bytes())
    receipt_path = checked(source / "Inspection/DistanceMateResults.json", BASE_RESULT, owner=source)
    checked(source / "DistanceMateHost01.json", HOST_SHA, owner=source)
    receipt = json.loads(receipt_path.read_bytes())
    before, rejected, after = receipt["phases"]
    require(receipt["packet_sha256"] == BASE_PACKET and not receipt["passed"] and receipt["controls_healthy"]
            and receipt["frozen_inputs_unchanged"] and receipt["frozen_packet_unchanged"] and before["passed"] and after["passed"]
            and rejected["label"] == "Generated" and rejected["opened"] and rejected["open_errors"] == 2 and rejected["open_warnings"] == 0,
            "original displacement control evidence differs")
    sources, encoded, observed = prove_path_pair(source, packet)
    output.mkdir()
    tools, frozen = output / "Tools", output / "FrozenGenerated"
    tools.mkdir()
    frozen.mkdir()
    for name, expected in packet["tool_hashes"].items():
        copyfile(checked(source / "Tools" / name, expected, owner=source / "Tools"), tools / name)
    for name in SOURCE_ARTIFACTS:
        incoming = checked(source / name, packet["generated"]["source_artifact_sha256"][name], owner=source)
        copyfile(incoming, output / name)
    for native in sources:
        copyfile(native, frozen / native.name)
    copyfile(original, output / "Trial.json")
    copyfile(SCRIPT, tools / SCRIPT.name)
    plan = output / "EncodedPaths.json"
    write_json(plan, {
        "schema": SCHEMA, "baseline_packet_sha256": BASE_PACKET, "baseline_native_result_sha256": BASE_RESULT,
        "baseline_host_transport_sha256": HOST_SHA, "source_preparer_sha256": digest(__file__), "observer_sha256": digest(SCRIPT),
        "generated_files": packet["generated"]["files"], "encoded_paths_by_file": encoded, "typed_file_references": observed,
        "read_only": True, "heldout_inputs_tested": 0, "native_acceptance": False,
    })
    sha = digest(plan)
    subprocess.run([sys.executable, "-B", str(tools / SCRIPT.name), "verify", str(plan), "--plan-sha256", sha],
                   check=True, timeout=25, capture_output=True)
    return {"plan": str(plan), "plan_sha256": sha, "observer_sha256": digest(SCRIPT), "preparer_sha256": digest(__file__)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Freeze a same-byte generated distance replay at the encoded Windows paths")
    parser.add_argument("baseline", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.baseline.resolve(strict=True), args.output.absolute()), sort_keys=True))
