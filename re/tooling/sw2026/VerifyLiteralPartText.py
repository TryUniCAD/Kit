from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
from subprocess import run
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
GENERATED = "SdkPartPropertiesNative02"
AUTHORED = "PartPropertySource01/Inspection"
CASES = {
    "PolygonGenerated": (
        f"{GENERATED}/PropertyPolygonDiscovery/PropertyPolygonDiscovery.SLDPRT",
        "0d3ec3a66fa50793bc54f18d2b9b16cf5aef7a58545f2cd527b2c1a240922062",
        f"{GENERATED}/PropertyPolygonDiscovery/Request.json",
    ),
    "CircleGenerated": (
        f"{GENERATED}/PropertyCircleDiscovery/PropertyCircleDiscovery.SLDPRT",
        "392c5b51b63761f4bba2baf6dc0715de4af8d3e5036b83a42e0f388031cc6edd",
        f"{GENERATED}/PropertyCircleDiscovery/Request.json",
    ),
    "PolygonSaved": (
        f"{GENERATED}/Inspection/polygonEdit/PropertyPolygonDiscoveryEdited.SLDPRT",
        "e311ba0626114291e62aacd26f705c8d304baa5d0315f89972fdde66bdee1f14",
        f"{GENERATED}/Inspection/polygonEdit/Record.json",
    ),
    "CircleSaved": (
        f"{GENERATED}/Inspection/circleEdit/PropertyCircleDiscoveryEdited.SLDPRT",
        "8007d21df3db5fc58c23d3fe589cfc15cf274ac83d9b2daa4878ee792e104e30",
        f"{GENERATED}/Inspection/circleEdit/Record.json",
    ),
    "CircleAuthored": (
        f"{AUTHORED}/CircularPropertiesAuthor/CircularProperties.SLDPRT",
        "1c1bc718661b88a119bc3ac041f97d56cf5b4a06e290e1ac1afc79d423e42d23",
        f"{AUTHORED}/CircularPropertiesAuthor/Record.json",
    ),
    "AdvancedRectangle": (
        f"{AUTHORED}/RectanglePropertiesAuthor/RectangleProperties.SLDPRT",
        "4377bf5680f30d1c9de52227928911e55604a75d30ceb987240df00d6b1b1805",
        None,
    ),
}
SUMMARY = "docProps/core.xml"
DOCUMENT = "docProps/custom.xml"
CONFIG = "docProps/Config-0-Properties.xml"
MANAGER = "Contents/CusProps"
DIRECTORY = "Contents/CMgrHdr2"
STATUS = "solidworks.part_text_properties"
DIAGNOSTIC = "solidworks.part_text_properties_unavailable"
SEMANTIC_HASH = "solidworks_source_semantic_sha256"
HOOK = "convert.adapters.solidworks.Core.Adapter.WithPartProps"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def literal_values(values):
    require(
        all(
            row["type"] == 30 and not row["linked"] and row["raw"] == row["resolved"]
            for row in values.values()
        ),
        "independent native observation is outside literal text",
    )
    return {name: row["raw"] for name, row in values.items()}


def expected_record(path):
    raw = path.read_bytes()
    data = json.loads(raw)
    if path.name == "Request.json":
        neutral = data["document"]
        (owner,) = neutral["configurations"]["$tuple"]
        return (
            owner["name"],
            neutral["metadata"]["document_summary"],
            neutral["metadata"]["custom_properties"],
            owner["attributes"]["custom_properties"],
        ), digest(raw)
    data = data["result"]
    rebuilt = data.get("states", data)["rebuilt"]
    return (
        rebuilt["configuration"],
        {name: value for name, value in rebuilt["summary"].items() if value},
        literal_values(rebuilt["document"]),
        literal_values(rebuilt["configured"]),
    ), digest(raw)


def without_projection(document):
    return replace(
        document,
        configurations=tuple(
            replace(
                config,
                attributes={
                    k: v
                    for k, v in config.attributes.items()
                    if k != "custom_properties"
                },
            )
            for config in document.configurations
        ),
        metadata={
            k: v
            for k, v in document.metadata.items()
            if k not in {STATUS, "document_summary", "custom_properties", SEMANTIC_HASH}
        },
        diagnostics=tuple(
            diag for diag in document.diagnostics if diag.code != DIAGNOSTIC
        ),
    )


def compare_document(document, baseline):
    from convert.adapters.solidworks.Core.Adapter import SemanticShaTwo

    expected = baseline.metadata[SEMANTIC_HASH]
    reduced = without_projection(document)
    require(
        reduced == without_projection(baseline),
        "property projection changed the ordinary document",
    )
    require(
        SemanticShaTwo(reduced) == expected,
        "property projection changed the ordinary semantic fingerprint",
    )


def old_read(read, asset, **kwargs):
    with patch(HOOK, side_effect=lambda document, archive: document):
        return read(asset, **kwargs)


def check_refusal(document, baseline):
    require(
        document.metadata[STATUS]["status"] == "unsupported",
        "unqualified text was accepted",
    )
    require(
        not ({"document_summary", "custom_properties"} & document.metadata.keys())
        and all(
            "custom_properties" not in config.attributes
            for config in document.configurations
        ),
        "unsupported input leaked a partial property bag",
    )
    require(
        sum(value.code == DIAGNOSTIC for value in document.diagnostics) == 1,
        "unsupported input lost its optional property diagnostic",
    )
    compare_document(document, baseline)
    return document.metadata[STATUS]["diagnostic"]


def exercise_mutations(archive, read, repack):
    from convert.adapters.solidworks.Archive.CmgrHeader.ReadMgrHeader import (
        ReadMgrHeader,
    )
    from convert.adapters.solidworks.Archive.CmgrHeader.WriteMgrHeader import (
        WriteMgrHeader,
    )
    from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue

    def altered_directory(field, value):
        graph = ReadMgrHeader(archive.require(DIRECTORY), 19000)
        (owner,) = graph.RootValue.FieldsValue["f08"]["items"]
        owner["o"].FieldsValue[field] = value
        return WriteMgrHeader(graph.RootValue, 19000)[0]

    config_raw = archive.require(CONFIG)
    custom_raw = archive.require(DOCUMENT)

    def replace_once(value, before, after):
        require(before in value, "disclosed property mutation anchor has changed")
        return value.replace(before, after, 1)

    prefix_end = config_raw.index(b"?>") + 2
    doc_type = (
        config_raw[:prefix_end]
        + b"\r\n<!DOCTYPE ConfigProperties>"
        + config_raw[prefix_end:]
    )
    cases = {
        "missing_saved_directory": {DIRECTORY: None},
        "missing_physical_config": {"Contents/Config-0": None},
        "mismatched_saved_id": {DIRECTORY: altered_directory("f30", 1)},
        "mismatched_saved_name": {
            DIRECTORY: altered_directory(
                "f10", CStringValue("Modified directory name", True)
            )
        },
        "inactive_saved_owner": {DIRECTORY: altered_directory("f08", 0)},
        "derived_saved_owner": {DIRECTORY: altered_directory("f34", 0)},
        "orphan_property_id": {
            CONFIG: None,
            "docProps/Config-1-Properties.xml": config_raw,
        },
        "noncanonical_property_id": {
            CONFIG: None,
            "docProps/Config-00-Properties.xml": config_raw,
        },
        "unqualified_encoding": {
            CONFIG: replace_once(config_raw, b'encoding="UTF-8"', b'encoding="UTF-16"')
        },
        "unqualified_doctype": {CONFIG: doc_type},
        "literal_type_mismatch": {
            DOCUMENT: replace_once(
                custom_raw,
                b'IsEquation="False" TypeID="0"',
                b'IsEquation="False" TypeID="30"',
            )
        },
        "broken_xml": {DOCUMENT: custom_raw[:-12]},
    }
    outcomes = {}
    for name, values in cases.items():
        mutated = repack(values)
        outcomes[name] = check_refusal(read(mutated), old_read(read, mutated))
    return outcomes


def public_refusal(read, asset, include_brep):
    try:
        read(asset, include_brep=include_brep)
    except ValueError as error:
        return str(error)
    raise ValueError("a pre-existing unsupported modeling profile changed")


def property_only(archive, read, path, expected_sha):
    from convert.adapters.solidworks.Core.Adapter import Configurations, NativePartModel
    from convert.adapters.solidworks.Core.Properties.WithPartProps import WithPartProps
    from interchange.document.Models.DocumentModel import CadDocument
    from interchange.Records.RecordSource import CadSource

    refusals = {}
    for include_brep, expected in (
        (True, "SLDPRT contains no readable Parasolid payload"),
        (False, "sketch sldprt:sketch:18 references missing plane"),
    ):
        actual = public_refusal(read, path, include_brep)
        baseline = public_refusal(
            lambda asset, **options: old_read(read, asset, **options),
            path,
            include_brep,
        )
        require(
            actual == baseline == expected,
            "generated fixture's prior public refusal differs",
        )
        refusals[str(include_brep).lower()] = actual
    subject = CadDocument(
        source=CadSource("solidworks.sldprt", "", expected_sha),
        configurations=Configurations(NativePartModel(archive, None), None),
        parameters=(),
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=(),
        bodies=(),
    )
    return WithPartProps(subject, archive), refusals


def inspect(root, case):
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import (
        BuildSldprt,
        SldprtArchive,
    )

    source, expected_sha, expected = CASES[case]
    path = root / source
    require(
        digest(path.read_bytes()) == expected_sha, "disclosed fixture identity changed"
    )
    archive = SldprtArchive.open(path)

    def read(asset, *, include_brep=True):
        return open_document(
            asset,
            source_format="solidworks.sldprt",
            strict=True,
            include_brep=include_brep,
            include_tessellation=False,
        )

    def repack(values):
        streams = dict(archive.streams)
        for name, item in values.items():
            if item is None:
                streams.pop(name, None)
            else:
                streams[name] = item
        return BuildSldprt(streams, FormatVersion=archive.format_version)

    manager = archive.get(MANAGER)
    row = {
        "case": case,
        "source_sha256": expected_sha,
        "saved_directory_sha256": digest(archive.require(DIRECTORY)),
        "native_property_manager_bytes": None if manager is None else len(manager),
    }
    if case.endswith("Generated"):
        actual, row["existing_public_refusals"] = property_only(
            archive, read, path, expected_sha
        )
        row["boundary"] = "typed_property_projection"
    else:
        actual = read(path)
        baseline = old_read(read, path)
        compare_document(actual, baseline)
        absent = repack({SUMMARY: None, DOCUMENT: None, CONFIG: None})
        unchanged = read(absent)
        require(
            unchanged == old_read(read, absent) and STATUS not in unchanged.metadata,
            "absent properties changed the normal path",
        )
        row.update(
            {
                "boundary": "public_document",
                "whole_document_baseline_equal": True,
                "brep_preserved": actual.brep is not None,
                "solid_body_count": sum(
                    body.topology.solid_count for body in actual.bodies
                ),
                "preserved_feature_rows": len(actual.feature_timeline),
                "preserved_sketches": len(actual.sketches),
                "preserved_parameters": len(actual.parameters),
            }
        )
        if expected is None:
            row["diagnostic"] = check_refusal(actual, baseline)
        if case == "CircleAuthored":
            row["refusals"] = exercise_mutations(archive, read, repack)
    row["status"] = actual.metadata[STATUS]["status"]
    if expected is not None:
        expected_values, expected_sha256 = expected_record(root / expected)
        (owner,) = actual.configurations
        values = (
            owner.name,
            actual.metadata["document_summary"],
            actual.metadata["custom_properties"],
            owner.attributes["custom_properties"],
        )
        require(
            owner.active and owner.attributes["native_configuration_id"] == 0,
            "active configuration identity changed",
        )
        require(
            actual.metadata[STATUS]["status"] == "complete"
            and values == expected_values,
            "public property dictionaries differ from independent values",
        )
        row["expected_record_sha256"] = expected_sha256
        row["qualified_fields"] = [len(scope) for scope in values[1:]]
    require(digest(path.read_bytes()) == expected_sha, "disclosed input changed")
    require(
        not any(name.startswith(("win32com", "pythoncom")) for name in sys.modules),
        "SDK crossed native runtime boundary",
    )
    return row


def main():
    parser = ArgumentParser(
        description="Check exact disclosed literal text through the public SDK"
    )
    parser.add_argument("disclosed_root", type=Path)
    parser.add_argument("--case", choices=CASES)
    args = parser.parse_args()
    if args.case is not None:
        print(json.dumps(inspect(args.disclosed_root, args.case), sort_keys=True))
        return
    rows = []
    environment = os.environ | {"PYTHONPATH": str(ROOT / "src")}
    for name in CASES:
        result = run(
            (
                sys.executable,
                "-B",
                str(Path(__file__).resolve()),
                str(args.disclosed_root),
                "--case",
                name,
            ),
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        require(result.returncode == 0, name + " failed\n" + result.stderr)
        rows.append(json.loads(result.stdout))
    print(
        json.dumps(
            {
                "schema": "kit.sw2026.literal-part-text-read.v1",
                "passed": True,
                "fresh_processes": len(rows),
                "native_processes_started": 0,
                "input_hashes_preserved": True,
                "cases": rows,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
