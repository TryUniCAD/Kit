from dataclasses import replace
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Drawing.Layout.MakeDrawDoc import MakeDrawDoc
from convert.adapters.solidworks.Drawing.Reading.Blank.ReadBlankIntent import (
    ReadBlankIntent,
)
from convert.adapters.solidworks.Drawing.Reading.Blank.Plain import Plain
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument


# a complete blank projection must retain native intent instead of merely suppressing the layout warning
def ReadBlankDraw(Archive: SldprtArchive, SourceData: bytes, Label: str) -> CadDocument:
    Value = ReadBlankIntent(Archive, SourceData)
    Input = Value.InputValue
    Document = MakeDrawDoc(
        Archive, SourceData, Label, Value.VersionValue, Input.DrawingValue
    )
    Attributes = dict(Document.source.attributes)
    Attributes.update(
        {
            "solidworks.blank.profile": "fresh-v19000-seven-stream-v1",
            "solidworks.blank.native_sheet_id": Value.NativeSheetId,
            "solidworks.blank.intent": Plain(Input),
            "solidworks.blank.style_language_selector_is_representative": True,
            "solidworks.blank.complete_stream_reconstruction": True,
            "solidworks.blank.complete_container_reconstruction": True,
        }
    )
    return replace(
        Document,
        source=replace(Document.source, attributes=FreezeMapping(Attributes)),
        diagnostics=(),
        metadata=FreezeMapping({"name": Input.OptionsValue.NameValue}),
    )
