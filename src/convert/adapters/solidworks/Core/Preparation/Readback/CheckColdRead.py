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
from interchange.document.Behavior.DocumentIo import ToJson
from interchange.document.Models.DocumentModel import CadDocument


# comparison covers every derived and retained field without making it an input to generation
def CheckColdRead(
    Document: CadDocument, Payload: bytes, *, IsEllipse: bool = False
) -> None:
    SourceName = Document.source.path
    Archive = SldprtArchive.from_bytes(Payload, SourceName)
    Model = (
        None
        if IsEllipse
        else DecodeNative(
            Archive.require(KeywordsStream),
            Archive.require(KResolvedFeaturesStream),
            Archive.require(KConfigStream),
            configuration_id=0,
            resolved_stream=KResolvedFeaturesStream,
            configuration_stream=KConfigStream,
        )
    )
    IncludeBrep = not IsEllipse or Document.brep is not None
    Expected = ReadNativePart(
        SldprtAdapter(),
        Archive,
        Payload,
        SourceName,
        ReadOptions(include_brep=IncludeBrep),
        ModelValue=None if Model is None else WithTypedNative(Model, Archive),
    )
    if (Expected.brep is not None) != IncludeBrep or ToJson(
        Document, IndentSize=None
    ) != ToJson(Expected, IndentSize=None):
        raise ValueError("SOLIDWORKS cold readback differs from its regenerated part")
