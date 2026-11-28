from __future__ import annotations

from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
import json
from pathlib import Path
import platform
import sys

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Resolved.ReadResolvedMut import ReadResolvedMut
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit


BASE_CLASS = "moBaseBody_c"
MANAGER = "Contents/CMgr"
HEADER = "Contents/Config-0-ModelHeader"
TOP_HEADER = "Header2"
OWNERS = (
    "re/tooling/sw2026/imported_body_source/ReplayTypedBaseBody.py",
    "src/convert/adapters/solidworks/Archive/Bodies/CheckBaseCtx.py",
    "src/convert/adapters/solidworks/Archive/Bodies/ValidateFields.py",
    "src/convert/adapters/solidworks/Archive/Bodies/Layouts/Resolved/ImportFields.py",
    "src/convert/adapters/solidworks/Archive/Bodies/Layouts/Resolved/ResolvedLayouts.py",
    "src/convert/adapters/solidworks/Archive/Bodies/Layouts/Resolved/ResolvedSchemas.py",
    "src/convert/adapters/solidworks/Archive/Bodies/Layouts/Resolved/ResolvedVirtuals.py",
    "src/convert/adapters/solidworks/Core/TypedResolved/ReadNativeLink.py",
)
ORIGINAL_RECEIPT = "re/solidworks/measurements/2026/ImportedBaseBodyWitnessReplay01.json"
CONTRAST_RECEIPT = "re/solidworks/measurements/2026/ImportedBodyNamesContrast01.json"


def require(condition, diagnostic):
    if not condition:
        raise ValueError(diagnostic)


def signature(data):
    return {"bytes": len(data), "sha256": sha256(data).hexdigest()}


def reject(operation, reason):
    try:
        operation()
    except BodyUnsupported as error:
        require(reason in str(error), f"unexpected refusal {error}")
        return str(error)
    raise ValueError(f"unqualified base body changed admission: {reason}")


def cstring(value):
    if type(value) is str:
        return {"encoding": "unicode", "text": value}
    if type(value) is tuple and len(value) == 2 and value[0] == "A" and type(value[1]) is str:
        return {"encoding": "ansi", "text": value[1]}
    raise TypeError("unrecognized typed CString representation")


def read_sources(repository, paths):
    original = json.loads((repository / ORIGINAL_RECEIPT).read_bytes())
    contrast = json.loads((repository / CONTRAST_RECEIPT).read_bytes())
    expect = {
        "Disclosed": (original["source_sha256"], original["matched_streams"]),
        **{case: (item["file_sha256"], item["linked_streams"]) for case, item in contrast["variants"].items()},
    }
    require(paths.keys() == expect.keys(), "use all four exact disclosed source paths")
    observed = {}
    for case, path in paths.items():
        raw = path.read_bytes()
        digests = signature(raw)
        expected, expected_streams = expect[case]
        require(digests["sha256"] == expected, f"disclosed source hash differs for {case}")
        observed[case] = (digests, SldprtArchive.from_bytes(raw), expected_streams)
    return observed


def guard_refusals(archive, link, previous, imported):
    version = link.ResolvedValue.VersionValue
    context = link.ResolvedValue.ContextValue
    wrong = {**context, "cmgr_f658": 0}
    graph = link.ResolvedValue

    def write(flags):
        return WriteResolMut(graph.RootsValue, graph.ExtraFields, version, previous, flags)

    controls = {
        "read_manager_mode_zero": reject(
            lambda: ReadResolvedMut(archive.require(link.StreamName), version, link.ConfigValue.MapValue, wrong),
            "unsupported ordinary base body archive context",
        ),
        "write_manager_mode_zero": reject(lambda: write(wrong), "unsupported ordinary base body archive context"),
    }
    field = "local_body_switch"
    old_switch = imported.FieldsValue[field]
    old_class = imported.ClassValue
    try:
        for mode in (0, 2, -1):
            imported.FieldsValue[field] = mode
            controls[f"write_local_mode_{mode}"] = reject(lambda: write(context), "unsupported base body storage mode")
        imported.FieldsValue[field] = old_switch
        imported.ClassValue = RuntimeClass(BASE_CLASS, 2)
        controls["write_schema_two"] = reject(lambda: write(context), "unsupported SOLIDWORKS body class moBaseBody_c schema 2")
    finally:
        imported.FieldsValue[field] = old_switch
        imported.ClassValue = old_class
    return controls


def replay(archive, expected_streams, measure_refusals):
    link = ReadNativeLink(archive, 0)
    version = link.ConfigValue.VersionValue
    config, regenerated_config = WriteConfigMut(link.ConfigValue.RootValue, version, link.ConfigValue.HeaderValue)
    previous = regenerated_config.MapValue
    graph = link.ResolvedValue
    resolved, regenerated_resolved = WriteResolMut(graph.RootsValue, graph.ExtraFields, version, previous, graph.ContextValue)
    manager = ReadCmgrMut(archive.require(MANAGER), version)
    streams = {
        "Contents/Config-0": config,
        "Contents/Config-0-ResolvedFeatures": resolved,
        MANAGER: WriteCmgrMut(manager.RootValue, version),
    }
    for name in (HEADER, TOP_HEADER):
        streams[name] = WriteHeadGraph(ReadHeaderGraph(archive.require(name), version), version)
    signatures = {}
    for name, stream in streams.items():
        require(stream == archive.require(name), f"production typed replay changed {name}")
        observed = signature(stream)
        recorded = expected_streams[name]
        require(all(observed[key] == recorded[key] for key in ("bytes", "sha256")),
                f"stream hash differs from disclosed native evidence for {name}")
        signatures[name] = observed
    require(previous.CounterValue == graph.MapBase
            and regenerated_resolved.MapValue.CounterValue == graph.MapValue.CounterValue,
            "typed replay changed the inherited or final resolved counter")
    imported, = (node for node in graph.RootsValue if node.ClassValue.NameValue == BASE_CLASS)
    fields = imported.FieldsValue
    atom, = (row["o"] for row in fields["f528"]["items"])
    mesh_ids = [row["feature_id"] for row in fields["segment_mesh_ids"]]
    require(fields["local_body_switch"] == 1 and fields["segment_mesh_count"] == len(mesh_ids) == 0,
            "original source is outside the measured plain local body profile")
    return {
        "configuration_map": previous.CounterValue, "resolved_map": graph.MapValue.CounterValue,
        "resolved_base": graph.MapBase, "linked_context": graph.ContextValue, "archive_version": version,
        "class": imported.ClassValue.NameValue, "runtime_schema": imported.ClassValue.SchemaValue,
        "feature_id": fields["f08"], "feature_name": ReadNativeName(imported),
        "source_filename": cstring(fields["source_filename"]),
        "local_body_switch": fields["local_body_switch"], "local_storage_key": cstring(fields["local_storage_key"]),
        "segment_mesh_count": fields["segment_mesh_count"], "segment_mesh_ids": mesh_ids,
        "explicit_atom_name": None if atom.FieldsValue["f18"] is None else ReadNativeName(atom),
        "streams": signatures,
        **({"intentional_refusals": guard_refusals(archive, link, previous, imported)} if measure_refusals else {}),
    }


def measure(repository, paths):
    sources = read_sources(repository, paths)
    for encoding in ("latin-1", "utf-16-le"):
        lookup(encoding)
    audit = BuildAudit(Path(__file__).resolve().parent)
    audit.BeginBuild()
    active = True

    def observe(event, arguments):
        if active:
            audit.InspectEvent(event, arguments)
            if event.startswith("socket.") or event == "ctypes.dlopen":
                raise PermissionError(f"typed base body replay attempted {event}")

    sys.addaudithook(observe)
    try:
        cases = {
            name: {"source": identity, **replay(archive, streams, name == "Disclosed")}
            for name, (identity, archive, streams) in sources.items()
        }
    finally:
        active = False
    return {
        "schema": "kit.sw2026.imported-base-body-typed-replay.v1",
        "oracle_source_build": "SOLIDWORKS 2026 SP05.2 34.5.2.0604",
        "production_context_unpatched": True,
        "cases": cases,
        "linked_streams_byte_exact": sum(len(case["streams"]) for case in cases.values()),
        "audited_replay_denied_accesses": len(audit.DeniedReads),
        "heldout_payloads_read": 0, "native_writer_outputs": 0, "native_writer_acceptance": False,
        "source_receipt_sha256": {name: signature((repository / name).read_bytes())["sha256"]
                                  for name in (ORIGINAL_RECEIPT, CONTRAST_RECEIPT)},
        "owning_source_sha256": {name: signature((repository / name).read_bytes())["sha256"] for name in OWNERS},
        "python": platform.python_version(),
    }


def main():
    parser = ArgumentParser(description="Replay the four disclosed base body graphs with ordinary production typed codecs")
    for option in ("disclosed", "other-shape", "renamed-feature", "renamed-body"):
        parser.add_argument("--" + option, type=Path, required=True)
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[4]
    paths = {"Disclosed": args.disclosed, "OtherShape": args.other_shape,
             "RenamedFeature": args.renamed_feature, "RenamedBody": args.renamed_body}
    print(json.dumps(measure(repository, paths), indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
