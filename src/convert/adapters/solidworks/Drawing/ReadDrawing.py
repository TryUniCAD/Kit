from pathlib import PureWindowsPath

from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KFormatIdBySuffix
from convert.adapters.solidworks.Container.SldprtFormat import SldprtFormat
from convert.adapters.solidworks.Drawing.Identity.DrawingIdentity import (
    CheckDrawLane,
    KDefinitionStream,
)
from convert.adapters.solidworks.Drawing.Layout.MakeDrawDoc import MakeDrawDoc
from convert.adapters.solidworks.Drawing.Layout.ReadDrawLayout import ReadDrawLayout
from interchange.document.Models.DocumentModel import CadDocument


# live drawing inspection remains explicit until every defining lane is supported
def ReadDrawing(
    Archive: SldprtArchive, DataValue: bytes, Label: str, Settings: ReadOptions
) -> CadDocument:
    if PureWindowsPath(Label).suffix.casefold() in KFormatIdBySuffix:
        raise SldprtFormat("SOLIDWORKS drawing content requires a .SLDDRW source")
    if Settings.strict:
        from convert.adapters.solidworks.Drawing.Reading.ReadGeneratedBlank import (
            ReadBlankDraw,
        )

        if Settings.configuration is not None:
            raise SldprtFormat(
                "drawing configuration selection belongs to the linked model view"
            )
        try:
            return ReadBlankDraw(Archive, DataValue, Label)
        except (KeyError, TypeError, ValueError, IndexError) as ErrorValue:
            raise SldprtFormat(
                "strict generated blank drawing is unsupported: " + str(ErrorValue)
            ) from ErrorValue
    if Settings.configuration is not None:
        raise SldprtFormat(
            "drawing configuration selection belongs to the linked model view"
        )
    try:
        from convert.adapters.solidworks.Drawing.Definition.Projection.JoinConcept import (
            JoinConcept,
        )
        from convert.adapters.solidworks.Drawing.Definition.ReadConcept import (
            ReadConcept,
        )

        from convert.adapters.solidworks.Drawing.Definition.PlainNotes.PlainNoteRequired import (
            PlainNoteError,
        )

        Version = CheckDrawLane(Archive)
        try:
            Concept = ReadConcept(Archive, Version)
        except PlainNoteError:
            from convert.adapters.solidworks.Drawing.Definition.PlainNotes.ReadNoteDrawing import (
                ReadNoteDrawing,
            )

            Layout = ReadNoteDrawing(
                Archive.require(KDefinitionStream),
                Version,
                ReadDrawLayout(Archive, Version),
            )
        else:
            Layout = JoinConcept(Concept, ReadDrawLayout(Archive, Version))
    except SldprtFormat:
        raise
    except (KeyError, TypeError, ValueError) as ErrorValue:
        raise SldprtFormat(
            f"invalid SOLIDWORKS drawing layout: {ErrorValue}"
        ) from ErrorValue
    return MakeDrawDoc(Archive, DataValue, Label, Version, Layout)
