from hashlib import sha256
from pathlib import Path
import json

from convert.adapters.solidworks.Archive.Bodies.RequireHistRef import RequireHistRef
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
from convert.adapters.solidworks.Archive.Mates.WriteMatesMut import WriteMatesMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


ROOT = Path(__file__).resolve().parents[3]
CORPUS = ROOT / "re/solidworks/v2026/corpus/assemblies"
ADAPTER = ROOT / "src/convert/adapters/solidworks"
VERSION = 19000
CONFIG = "Contents/Config-0"
RESOLVED = CONFIG + "-ResolvedFeatures"
MATES = CONFIG + "-MatesList"
HISTORY_CLASS = RuntimeClass("moHistoryCompItemData_c", 1)
CASE_PROFILES = {
    "A0_one.SLDASM": {
        "sha256": "66965b66e14bacb506b147fa354e6708aa207c7589efbf8e5f3d3fbe7cf453f8",
        "streams": ((24828, 103), (5444, 172), (6, 172)),
        "history_slots": ((113, 115, 117, 119),),
        "mate_classes": (),
    },
    "A1_two.SLDASM": {
        "sha256": "594559a38ea2a077850a823e808ed7f79c559bfac743eab7c9ab4aa75cf252e4",
        "streams": ((25338, 108), (5500, 181), (10411, 250)),
        "history_slots": ((118, 120, 122, 124), (125, 126, 127, 128)),
        "mate_classes": ("moMateCoincident", "moMateDistanceDim_c", "moMateCoincident"),
    },
}
CODEC_OWNERS = (
    "Archive/Bodies/CheckBodyMut.py",
    "Archive/Bodies/Layouts/ReferenceFields.py",
    "Archive/Bodies/Layouts/Resolved/ComponentFields.py",
    "Archive/Bodies/Layouts/Resolved/ResolvedLayouts.py",
    "Archive/Bodies/Layouts/Resolved/ResolvedSchemas.py",
    "Archive/Bodies/Layouts/Resolved/ResolvedVirtuals.py",
    "Archive/Bodies/ReadBodyMut.py",
    "Archive/Bodies/Reading/ReadHistRefMut.py",
    "Archive/Bodies/Reading/ReadValueMut.py",
    "Archive/Bodies/RequireHistRef.py",
    "Archive/Bodies/WriteBodyMut.py",
    "Archive/Bodies/Writing/WriteValueMut.py",
    "Archive/Cmgr/ReadCmgrMut.py",
    "Archive/Config/ReadConfigMut.py",
    "Archive/Config/WriteConfigMut.py",
    "Archive/Header/ReadNativeHeader.py",
    "Archive/Maps/ArchiveMaps.py",
    "Archive/Maps/MapEntry.py",
    "Archive/Maps/MapSnapshot.py",
    "Archive/Mates/MakeMatesCtx.py",
    "Archive/Mates/MatesSchemas.py",
    "Archive/Mates/ReadMatesMut.py",
    "Archive/Mates/WriteMatesMut.py",
    "Archive/Reading/ReadGraphNode.py",
    "Archive/Resolved/MakeResolvedCtx.py",
    "Archive/Resolved/ReadResolvedMut.py",
    "Archive/Resolved/WriteResolMut.py",
    "Container/Container.py",
    "Core/TypedResolved/ReadNativeLink.py",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify_stream(name, archived, emitted, read, written, expected):
    require(emitted == archived, f"{name}: encoded bytes changed")
    require(read.MapValue.CounterValue == written.MapValue.CounterValue, f"{name}: map counter changed")
    require((len(archived), read.MapValue.CounterValue) == expected, f"{name}: measured profile changed")
    for direction in (read, written):
        report = direction.ReportValue
        require(report["completed"] and not report["missing_schemas"] and not report["provisional_schemas"],
                f"{name}: incomplete typed codec")
    return {
        "bytes": len(archived),
        "sha256": sha256(archived).hexdigest(),
        "encoded_sha256": sha256(emitted).hexdigest(),
        "map_count": read.MapValue.CounterValue,
        "byte_identity": True,
    }


def verify_history(read, written, expected):
    original = {entry.IndexValue: entry.EntryValue for entry in read.MapValue.EntriesValue}
    reproduced = {entry.IndexValue: entry.EntryValue for entry in written.MapValue.EntriesValue}
    history = [node for _, node in sorted(original.items())
               if isinstance(node, ArchiveNode) and node.ClassValue == HISTORY_CLASS]
    links = []
    for entry in history:
        chain = RequireHistRef(entry.FieldsValue["f48"])
        assembly = chain.FieldsValue["owner"]
        reference = chain.FieldsValue["f20"]
        require(isinstance(assembly, ArchiveNode) and assembly.ClassValue == RuntimeClass("moAssembly_c", 1),
                "history chain lost its concrete assembly owner")
        require(isinstance(reference, ArchiveNode) and reference.ClassValue == RuntimeClass("moReferenceChain_c", 1),
                "history chain changed its reference class")
        list_node = reference.FieldsValue["f08"]
        require(isinstance(list_node, ArchiveNode) and list_node.ClassValue == RuntimeClass("moExtFeatureList_c", 1),
                "history reference changed its feature-list class")
        for node in (entry, assembly, chain, reference, list_node):
            require(original.get(node.IndexValue) is node and reproduced.get(node.IndexValue) is node,
                    "history reference lost its shared map identity")
        links.append((entry.IndexValue, chain.IndexValue, reference.IndexValue, list_node.IndexValue))
    require(tuple(links) == expected, "history reference slots changed")
    return [
        {
            "history_index": history_index,
            "chain_index": chain_index,
            "reference_index": reference_index,
            "feature_list_index": list_index,
            "shared_identity": True,
        }
        for history_index, chain_index, reference_index, list_index in links
    ]


def inspect_case(name, profile, declaration):
    data = (CORPUS / name).read_bytes()
    digest = sha256(data).hexdigest()
    require(digest == declaration["sha256"] == profile["sha256"], f"{name}: disclosed fixture changed")
    archive = SldprtArchive.from_bytes(data)
    source = ReadNativeLink(archive, 0)
    config = source.ConfigValue
    resolved = source.ResolvedValue
    mates = ReadMatesMut(archive.require(MATES), resolved)
    config_bytes, stored_config = WriteConfigMut(config.RootValue, VERSION, config.HeaderValue)
    resolved_bytes, stored_resolved = WriteResolMut(
        resolved.RootsValue, resolved.ExtraFields, VERSION, stored_config.MapValue, resolved.ContextValue
    )
    mate_bytes, stored_mates = WriteMatesMut(mates.RootsValue, stored_resolved)
    streams = {}
    for stream, emitted, decoded, stored, expected in zip(
        (CONFIG, RESOLVED, MATES), (config_bytes, resolved_bytes, mate_bytes),
        (config, resolved, mates), (stored_config, stored_resolved, stored_mates), profile["streams"], strict=True,
    ):
        streams[stream] = verify_stream(stream, archive.require(stream), emitted, decoded, stored, expected)
    classes = tuple(node.ClassValue.NameValue for node in mates.RootsValue)
    require(classes == profile["mate_classes"], f"{name}: mate roots changed")
    return {
        "fixture_sha256": digest,
        "fixture_bytes": len(data),
        "original_native_source_sha256": declaration["source_sha256"],
        "source_native_revision": declaration["revision"],
        "archive_version": resolved.VersionValue,
        "streams": streams,
        "history_references": verify_history(resolved, stored_resolved, profile["history_slots"]),
        "mate_classes": classes,
    }


def main():
    manifest = (CORPUS / "Manifest.json").read_bytes()
    declarations = {item["name"]: item for item in json.loads(manifest)["records"]}
    evidence = {
        "schema": "kit.sw2026.sdk-history-component-roundtrip.v1",
        "scope": "two disclosed version-19000 assembly source controls",
        "source_manifest_sha256": sha256(manifest).hexdigest(),
        "observer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "codec_owner_sha256": {name: sha256((ADAPTER / name).read_bytes()).hexdigest() for name in CODEC_OWNERS},
        "verified_streams": 6,
        "cases": {name: inspect_case(name, profile, declarations[name]) for name, profile in CASE_PROFILES.items()},
    }
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
