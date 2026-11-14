from __future__ import annotations as Annotations

from dataclasses import replace as Replace
from io import BytesIO as BytesIo
from typing import cast as CastValue


from convert.adapters import AdapterRegistry, CadAdapter, ReadOptions, WriteOptions
from convert.adapters.nx import NxAdapter, ProbeNx, ReadNx, WriteNx
from convert.adapters.nx.SplmBuild import BuildSplm
from interchange import FeatureKind

# the synthetic payload keeps integration coverage free of vendor saved files
KPartPayload = (
    (0).to_bytes(12, "little")
    + (1).to_bytes(4, "little")
    + (1).to_bytes(4, "little")
    + (24).to_bytes(4, "little")
)

# the synthetic attributes exercise equal length native metadata replacement
KAttributes = (
    b'<?xml version="1.0"?><UgAttributes version="4">'
    b'<Attribute owner="part" title="NX_ReferenceSet" utf8title="NX_ReferenceSet" '
    b'value="Empty" utf8value="Empty" version="3"/>'
    b"</UgAttributes>"
)


# a complete modern container proves reader and writer behavior at the file boundary
def SyntheticPart() -> bytes:
    return BuildSplm(
        [
            ("/Root/", None),
            ("/Root/part/", None),
            ("/Root/UG_PART/", None),
            ("/Root/part/attrs", KAttributes),
            ("/Root/UG_PART/UG_PART", KPartPayload),
        ],
        FileTag=0x2BBA,
    )


# registry discovery must expose the independent reader and writer together
def TestNxDiscovery() -> None:
    Registry = AdapterRegistry()
    _ = Registry.introspect("convert.adapters")
    assert "siemens.nx" in {Adapter.info.format_id for Adapter in Registry.readers()}
    assert "siemens.nx" in {Adapter.info.format_id for Adapter in Registry.writers()}
    assert isinstance(NxAdapter(), CadAdapter)


# probing must accept the modern signature and reject unrelated bytes
def TestNxProbe() -> None:
    assert ProbeNx(SyntheticPart()).confidence == 1.0
    assert ProbeNx(b"not an nx part").confidence == 0.0


# reading must retain native features and project equal length attributes
def TestNxRead() -> None:
    Document = ReadNx(SyntheticPart(), ReadOptions(strict=False))
    assert Document.source.format_id == "siemens.nx"
    assert Document.metadata["nx.container"] == "SPLMSSTR"
    Attributes = CastValue(dict[str, str], Document.metadata["nx.attributes"])
    assert Attributes["NX_ReferenceSet"] == "Empty"
    assert len(Document.feature_timeline) == 1
    assert (
        CastValue(FeatureKind, Document.feature_timeline[0].kind) == FeatureKind.KNative
    )
    assert Document.bodies == ()


# writing must rebuild the container and reject header changing edits
def TestNxWrite() -> None:
    Document = ReadNx(SyntheticPart(), ReadOptions(strict=False))
    Changed = Replace(
        Document,
        metadata={
            **Document.metadata,
            "nx.attribute_overrides": {"NX_ReferenceSet": "KitNX"},
        },
    )
    Output = BytesIo()
    Result = WriteNx(Changed, Output, WriteOptions())
    assert Result.vendor_loadable is True
    assert Result.application_usable is True
    assert len(Output.getvalue()) == len(SyntheticPart())
    Restored = ReadNx(Output.getvalue(), ReadOptions(strict=False))
    Attributes = CastValue(dict[str, str], Restored.metadata["nx.attributes"])
    assert Attributes["NX_ReferenceSet"] == "KitNX"
    try:
        _ = WriteNx(
            Replace(
                Document,
                metadata={
                    **Document.metadata,
                    "nx.attribute_overrides": {"NX_ReferenceSet": "too long"},
                },
            ),
            BytesIo(),
            WriteOptions(),
        )
    except ValueError as ErrorInfo:
        assert "preserve value byte length" in str(ErrorInfo)
    else:
        raise AssertionError("header changing NX edit was accepted")
