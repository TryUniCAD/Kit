from io import BytesIO as BytesStream
from zipfile import ZipFile as ZipReader

from convert.Formats.Fusion.ContainerCodec.ContainerLayout import KAssetPrefix
from convert.Formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from tests.Convert.Api.Fusion.SavedConfig.CheckCfgRoots import CheckCfgRoots


# archive checks keep physical role order and serializer ownership observable after generation
def ReadConfigRoles(Payload: bytes) -> tuple[tuple[str, str], ...]:
    Model = ReadDocument(Payload)
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
    CheckCfgRoots(Model, Parts)
    return Parts
