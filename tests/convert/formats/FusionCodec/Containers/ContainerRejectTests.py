from dataclasses import replace as Replace
from io import BytesIO
from pathlib import Path as FilePath
from zipfile import ZipFile

from pytest import mark as TestMarks, raises as RaiseError

from convert.formats.Fusion.ContainerCodec.EmitContainer import EmitContainer
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.ContainerCodec.ReadContainer import ReadContainer
from convert.formats.Fusion.SegmentCodec.Manifest.EmitRootWire import EmitRootWire
from convert.formats.Fusion.SegmentCodec.Manifest.ReadRootWire import ReadRootWire
from convert.formats.Fusion.SegmentCodec.Metadata.ReadMetaWire import ReadMetaWire
from convert.formats.Fusion.SegmentCodec.Metadata.WriteMetaWire import WriteMetaWire
from tests.convert.formats.FusionCodec.Containers.MakeContainer import MakeContainer


@TestMarks.parametrize(
    "Mutation",
    (
        "directory",
        "unknown",
        "case_alias",
        "identity",
        "watermark",
        "offsets",
        "preview",
    ),
)
def TestRejectFile(TmpPath: FilePath, Mutation: str) -> None:
    Source = EmitContainer(MakeContainer())
    with ZipFile(BytesIO(Source)) as Archive:
        Members = {Entry.filename: Archive.read(Entry) for Entry in Archive.infolist()}
    if Mutation == "directory":
        del Members["FusionAssetName[Active]/Breps.BlobParts/"]
    elif Mutation == "unknown":
        Members["Unknown.dat"] = b"uninterpreted"
    elif Mutation == "case_alias":
        Members["manifest.dat"] = Members["Manifest.dat"]
    elif Mutation == "identity":
        RootValue = ReadRootWire(Members["Manifest.dat"])
        Members["Manifest.dat"] = EmitRootWire(
            Replace(RootValue, AssetId="31415926-1111-4222-8333-0123456789ab")
        )
    elif Mutation == "watermark":
        NameValue = "FusionAssetName[Active]/Manifest.dat"
        Payload = Members[NameValue]
        Marker = b"\0\0\0\0\3\0\0\0\3\0\0\0"
        assert Payload.count(Marker) == 1
        Members[NameValue] = Payload.replace(Marker, b"\0" * 8 + b"\3\0\0\0")
    elif Mutation == "offsets":
        NameValue = "FusionAssetName[Active]/FusionDesignSegmentType1/MetaStream.dat"
        Metadata = ReadMetaWire(Members[NameValue])
        First, Second, *Following = Metadata.Primary
        Primary = (
            Replace(First, Offset=Second.Offset),
            Replace(Second, Offset=First.Offset),
            *Following,
        )
        Members[NameValue] = WriteMetaWire(Replace(Metadata, Primary=Primary))
    elif Mutation == "preview":
        NameValue = "FusionAssetName[Active]/Previews/small.png"
        Members[NameValue] = Members[NameValue][:-1]
    Target = TmpPath / "Malformed.f3d"
    with ZipFile(Target, "w") as Archive:
        for NameValue, Payload in Members.items():
            Archive.writestr(NameValue, Payload)
    with RaiseError(ValueError):
        _ = ReadContainer(Target.read_bytes())


@TestMarks.parametrize(
    "PartName",
    (
        "../Escape",
        "Images.BlobParts/../Escape",
        "Images.BlobParts/CON.png",
        "Images.BlobParts/Independent.png",
    ),
)
def TestRejectParts(TmpPath: FilePath, PartName: str) -> None:
    Value = MakeContainer()
    Invalid = Replace(Value, Parts=(*Value.Parts, ContainerPart(PartName, b"")))
    Target = TmpPath / "Invalid.f3d"
    with RaiseError(ValueError):
        _ = Target.write_bytes(EmitContainer(Invalid))
    assert not Target.exists()
