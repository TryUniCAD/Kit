from convert.adapters.solidworks.Archive.Construction.Metadata.MakeBiography import (
    MakeBiography,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeFreshHist import (
    MakeFreshHist,
)
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.History.WriteHistMut import WriteHistMut
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar
from convert.adapters.solidworks.Container.Format import KeywordsStream
from convert.adapters.solidworks.Drawing.Construction.Portable.BlankDrawInput import (
    BlankDrawInput,
)
from convert.adapters.solidworks.Drawing.Metadata.Writing.MakeSheetKeys import (
    MakeSheetKeys,
)
from convert.adapters.solidworks.Drawing.Metadata.Writing.MakeSheetProps import (
    MakeSheetProps,
)
from convert.adapters.solidworks.Drawing.Metadata.Writing.ReadSheetIndex import (
    ReadSheetIndex,
)


# every blank drawing metadata stream must derive from actual constructed owners and shared typed serializers without research imports
def MakeDrawStreams(
    InputValue: BlankDrawInput,
    HeaderValue: ArchiveNode,
    SheetValue: ArchiveNode,
    DefinitionValue: bytes,
) -> dict[str, bytes]:
    VersionValue = InputValue.UiSettings.VersionValue
    VersionPath = "_MO_VERSION_" + str(VersionValue) + "/"
    IndexValue = ReadSheetIndex(SheetValue)
    Biography, _ = WriteHistMut(MakeBiography(), VersionValue)
    HistoryValue, _ = WriteHistMut(MakeFreshHist(InputValue.HistoryValue), VersionValue)
    return {
        "Header2": WriteHeadGraph(HeaderValue, VersionValue),
        VersionPath + "Biography": Biography,
        VersionPath + "History": HistoryValue,
        "Contents/Definition": DefinitionValue,
        "ModelStamps": b"".join(
            EncodeScalar(HeaderValue.FieldsValue[FieldName], "u32")
            for FieldName in ("f70", "f40", "f44")
        ),
        KeywordsStream: MakeSheetKeys(
            InputValue.OptionsValue.NameValue,
            InputValue.OptionsValue.CreatedAt,
            IndexValue,
        ),
        "docProps/ISolidWorksInformation.xml": MakeSheetProps(IndexValue),
    }
