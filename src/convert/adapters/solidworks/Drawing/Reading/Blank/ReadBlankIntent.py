from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.History.ReadHistMut import ReadHistMut
from convert.adapters.solidworks.Archive.History.WriteHistMut import WriteHistMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Drawing.Construction.Portable.BlankDrawInput import (
    BlankDrawInput,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.MakeBlankFile import (
    MakeBlankFile,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.ReadBlankDef import (
    ReadBlankDef,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.WriteBlankDef import (
    WriteBlankDef,
)
from convert.adapters.solidworks.Drawing.Identity.DrawingIdentity import CheckDrawLane
from convert.adapters.solidworks.Drawing.Layout.ReadDrawLayout import ReadDrawLayout
from interchange.document.Models.Drawing.DrawingData import DrawingData
from interchange.document.Models.Drawing.DrawingSheet import DrawingSheet
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptNode as Node,
    NeedDrawNumber as Number,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ReadConceptName import (
    ReadConceptName as Name,
)
from convert.adapters.solidworks.Drawing.Reading.Blank.BlankIntent import BlankIntent
from convert.adapters.solidworks.Drawing.Reading.Blank.Integer import Integer
from convert.adapters.solidworks.Drawing.Reading.Blank.Require import Require
from convert.adapters.solidworks.Drawing.Reading.Blank.ReadBlankHistory import (
    ReadBlankHistory,
)
from convert.adapters.solidworks.Drawing.Reading.Blank.ReadBlankHeader import (
    ReadBlankHeader,
)
from convert.adapters.solidworks.Drawing.Reading.Blank.ReadBlankOptions import (
    ReadBlankOptions,
)
from convert.adapters.solidworks.Drawing.Reading.Blank.ReadBlankUi import ReadBlankUi
from convert.adapters.solidworks.Drawing.Reading.Blank.BlankStreamNames import (
    KBlankStreamNames,
)


# strict blank reading requires complete regeneration so no unmodeled source owner can be silently discarded
def ReadBlankIntent(Archive: SldprtArchive, SourceData: bytes) -> BlankIntent:
    Require(
        set(Archive.streams) == set(KBlankStreamNames),
        "strict blank profile requires exactly its seven generated streams",
    )
    Version = CheckDrawLane(Archive)
    Definition = ReadBlankDef(
        Archive.require("Contents/Definition"), Version
    ).GraphValue
    Require(
        WriteBlankDef(Definition).OutputValue == Archive.require("Contents/Definition"),
        "blank Definition does not re-emit exactly",
    )
    Document = Definition.DocumentValue
    Model = Node(Document.FieldsValue["model"], "moDrawing_c")
    HeaderNode = Node(Model.FieldsValue["fa8"], "moHeader_c")
    HeaderCopy = ReadHeaderGraph(Archive.require("Header2"), Version)
    Require(
        WriteHeadGraph(HeaderCopy, Version)
        == Archive.require("Header2")
        == WriteHeadGraph(HeaderNode, Version),
        "blank header copies or wire encoding differ",
    )
    Biography = ReadHistMut(Archive.require("_MO_VERSION_19000/Biography"), Version)
    History = ReadHistMut(Archive.require("_MO_VERSION_19000/History"), Version)
    for Label, Value in (("Biography", Biography), ("History", History)):
        Require(
            WriteHistMut(Value.RootValue, Version)[0]
            == Archive.require("_MO_VERSION_19000/" + Label),
            "blank chronology does not re-emit exactly",
        )
    HistoryInput = ReadBlankHistory(History.RootValue)
    HeaderInput, FileInput = ReadBlankHeader(HeaderNode, HistoryInput)
    Sheet = Node(Model.FieldsValue["f1430"], "moDrSheet")
    NativeId = Integer(Sheet.FieldsValue["f08"])
    SheetId = "slddrw:sheet:" + str(NativeId)
    First, Second = (Number(Sheet.FieldsValue[Key]) for Key in ("f3f8", "f400"))
    Require(
        First.is_integer() and Second.is_integer(),
        "blank scale terms are not positive integral native inputs",
    )
    Drawing = DrawingData(
        SheetId,
        (
            DrawingSheet(
                SheetId,
                Name(Sheet),
                Number(Sheet.FieldsValue["f3f0"]),
                Number(Sheet.FieldsValue["f3e8"]),
                (First, Second),
                (),
            ),
        ),
        (),
    )
    Layout = ReadDrawLayout(Archive, Version)
    Require(
        Layout.ActiveSheetId == SheetId
        and len(Layout.Sheets) == 1
        and Layout.Sheets[0].EntityName == Name(Sheet)
        and not Layout.ModelRefs
        and not Layout.Sheets[0].Views,
        "blank metadata and actual active sheet disagree",
    )
    Input = BlankDrawInput(
        Drawing,
        ReadBlankOptions(Model, HeaderInput.CreatedAt, HistoryInput.LanguageId),
        ReadBlankUi(Document),
        HeaderInput,
        FileInput,
        HistoryInput,
    )
    Generated = MakeBlankFile(Input)
    for Key in KBlankStreamNames:
        Require(
            Generated.StreamsValue[Key] == Archive.require(Key),
            "strict blank profile has an unrepresented owner in " + Key,
        )
    Require(
        Generated.BytesValue == SourceData,
        "strict blank profile has unrepresented container framing",
    )
    return BlankIntent(Input, NativeId, Version)
