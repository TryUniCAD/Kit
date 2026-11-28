from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeader
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KPartFormatId, KeywordsStream
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Drawing.Layout.ReadViewLayout import ReadViewLayout
from convert.adapters.solidworks.Drawing.Metadata.JoinModelRef import JoinModelRef
from convert.adapters.solidworks.Drawing.Metadata.JoinSheetProps import JoinSheetProps
from convert.adapters.solidworks.Drawing.Metadata.ReadDrawKeywords import (
    ReadSheetKeys,
)
from convert.adapters.solidworks.Drawing.Metadata.ReadDrawProps import ReadDrawProps
from interchange.document.Models.Drawing.DrawingData import DrawingData
from interchange.document.Models.Drawing.DrawingModelRef import DrawingModelRef
from interchange.document.Models.Drawing.DrawingSheet import DrawingSheet

# the current layout needs a closed set of documented package properties
KLayoutProperties = frozenset(
    {
        "SW-Current Sheet",
        "SW-Total Sheets",
        "SW-Sheet Name",
        "SW-All Sheet Names",
        "SW-All Sheet Format Data",
        "SW-Config-Model-View-Sheet-List",
    }
)


# combining independently decoded header and keyword owners preserves layout identity
def ReadDrawLayout(Archive: SldprtArchive, Version: int) -> DrawingData:
    Header = ReadHeader(Archive.require("Header2"), Version)
    if Header.SelfFile.KindValue != 4:
        raise SldprtFormat("drawing Definition and native header kind disagree")
    Sheet = ReadSheetKeys(Archive.require(KeywordsStream))
    Props = ReadDrawProps(
        Archive.require("docProps/ISolidWorksInformation.xml"), KLayoutProperties
    )
    Width, Height = JoinSheetProps(Props, Sheet)
    Model = JoinModelRef(Header, Sheet, Props["SW-Config-Model-View-Sheet-List"])
    SheetId = f"slddrw:sheet:{Sheet.IdValue}"
    ModelId = "slddrw:model:1"
    Views = () if Model is None else (ReadViewLayout(Header, Sheet, ModelId),)
    ModelRefs = (
        ()
        if Model is None
        else (DrawingModelRef(ModelId, Model.PathValue, KPartFormatId),)
    )
    return DrawingData(
        ActiveSheetId=SheetId,
        Sheets=(
            DrawingSheet(
                SheetId, Sheet.NameValue, Width, Height, Sheet.ScaleRatio, Views
            ),
        ),
        ModelRefs=ModelRefs,
    )
