from __future__ import annotations

from base64 import b64encode as EncodeBytes
from codecs import lookup as FindCodec
from importlib import import_module as ImportModule
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from sys import addaudithook as AddAuditHook, argv as ArgValues, path as ImportPaths
from sys import stdin as InputStream
from typing import cast as CastValue

KRepoRoot = FilePath(ArgValues[1])
ImportPaths.insert(0, str(KRepoRoot))
ImportPaths.insert(0, str(KRepoRoot / "src"))
ImportPaths.insert(0, str(KRepoRoot / "re" / "tooling" / "sw2026"))
ImportPaths.insert(0, str(KRepoRoot / "re" / "tooling" / "sw2026" / "serial"))

from tests.convert.solidworks.research.ConstructionGuard import BuildAudit

KAuditValue = BuildAudit(KRepoRoot / "re" / "tooling" / "sw2026" / "serial" / "defs")
AddAuditHook(KAuditValue.InspectEvent)
KConstruct = ImportModule("builders.Part").construct_part
KRegistry = ImportModule("Classes").registry()
KContainer = ImportModule("convert.adapters.solidworks.container.Container")
KRoundTrip = ImportModule("RoundTrip")
KCodecs = tuple(FindCodec(Value) for Value in ("utf-16-le", "utf-8", "latin-1"))
KRequest = CastValue(dict[str, object], LoadJson(InputStream.read()))
KAuditValue.BeginBuild()


def BuildResult() -> dict[str, object]:
    Constructed = KConstruct(registry=KRegistry, **KRequest)
    BlobValue = KContainer.build_sldprt(Constructed.streams)
    Archive = KContainer.SldprtArchive.from_bytes(BlobValue)
    Results = {
        NameValue: KRoundTrip.stream_roundtrip(
            Archive, NameValue, KRegistry, {**KRoundTrip.PLANS, **KRegistry.plans}, True
        )
        for NameValue in Constructed.streams
        if NameValue != "swXmlContents/KeyWords"
    }
    return {
        "blob": EncodeBytes(BlobValue).decode("ascii"),
        "streams": Results,
        "sizes": {
            NameValue: len(BytesValue)
            for NameValue, BytesValue in Constructed.streams.items()
        },
        "next_id": Constructed.next_id,
        "map_count": Constructed.configuration_map_count,
        "features": [Feature.cls for Feature in Constructed.features],
        "points": Constructed.extrusion.profile.point_count,
        "lines": Constructed.extrusion.profile.line_count,
        "depth": Constructed.extrusion.depth,
        "module_reads": KAuditValue.ModuleReads,
        "denied_reads": KAuditValue.DeniedReads,
        "vendor_acceptance": "unverified",
    }


print(DumpJson(BuildResult()))
