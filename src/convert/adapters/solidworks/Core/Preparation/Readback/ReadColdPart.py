from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import (
    KConfigStream,
    KeywordsStream,
    KResolvedFeaturesStream,
)
from convert.adapters.solidworks.Core.Adapter import ReadNativePart, SldprtAdapter
from convert.adapters.solidworks.Core.Native import DecodeNative
from convert.adapters.solidworks.Core.TypedResolved.WithTypedNative import (
    WithTypedNative,
)
from interchange.document.Models.DocumentModel import CadDocument


# a generated cache free part can be decoded through the ordinary public semantic projection from memory
def ReadColdPart(Payload: bytes, SourceName: str, Settings: ReadOptions) -> CadDocument:
    Archive = SldprtArchive.from_bytes(Payload, SourceName)
    Model = DecodeNative(
        Archive.require(KeywordsStream),
        Archive.require(KResolvedFeaturesStream),
        Archive.require(KConfigStream),
        configuration_id=0,
        resolved_stream=KResolvedFeaturesStream,
        configuration_stream=KConfigStream,
    )
    return ReadNativePart(
        SldprtAdapter(),
        Archive,
        Payload,
        SourceName,
        Settings,
        ModelValue=WithTypedNative(Model, Archive),
    )
