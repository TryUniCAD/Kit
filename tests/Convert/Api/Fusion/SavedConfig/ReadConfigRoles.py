from io import BytesIO as BytesStream
from pathlib import PurePosixPath as AssetPath
from zipfile import ZipFile as ZipReader

from convert.adapters.Fusion.Native.Graph.BuildGraph import BuildGraph
from convert.Formats.Fusion.ContainerCodec.ContainerLayout import KAssetPrefix
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument


# archive checks keep physical role order and serializer ownership observable after generation
def ReadConfigRoles(Payload: bytes) -> tuple[tuple[str, str], ...]:
    Model = ReadDocument(Payload)
    Graph = BuildGraph(Model)
    Parts = tuple(
        (PartValue.KindValue, PartValue.Name) for PartValue in Model.Configurations
    )
    Prefix = f"{KAssetPrefix}DesignConfigurationTable.BlobParts/"
    with ZipReader(BytesStream(Payload)) as Archive:
        Names = tuple(
            Member.removeprefix(KAssetPrefix)
            for Member in Archive.namelist()
            if Member.startswith(Prefix) and not Member.endswith("/")
        )
        assert Names == tuple(NameValue for _, NameValue in Parts)
        assert all(
            Archive.read(f"{KAssetPrefix}{NameValue}") == b"{}" for NameValue in Names
        )
    for RoleName in ("table", "rule"):
        RootName = f"DesignConfiguration{RoleName.title()}SerializerTrigger"
        Known = tuple(
            NameValue for PartRole, NameValue in Parts if PartRole == RoleName
        )
        Roots = Graph.ByClass(RootName)
        assert len(Roots) == len(Known)
        for Owner, NameValue in zip(Roots, Known, strict=True):
            assert Owner.SegmentId == 0 and Owner.Frame.RootId == RootName
            assert dict(Owner.Fields) == {"partName": AssetPath(NameValue).name}
    return Parts
