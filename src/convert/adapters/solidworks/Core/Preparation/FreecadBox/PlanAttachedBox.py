from dataclasses import dataclass as MakeDataClass

from convert.adapters.freecad.Native import DecodeNativeDoc
from convert.adapters.freecad.Replay.NativeDocPair import NativeDocPair
from convert.adapters.freecad.Replay.ReadNativeArc import ReadNativeArc
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.BoxOriginAxes import (
    BoxOriginAxes,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.BoxSource import (
    BoxSource,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxRelease import (
    ReadBoxRelease,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxSource import (
    ReadBoxSource,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadOriginAxes import (
    ReadOriginAxes,
)
from interchange.document.Models.DocumentModel import CadDocument


# keeping the original beside the target intent makes untranslated owners explicit
@MakeDataClass(frozen=True, slots=True)
class AttachedBoxPlan:
    SourceDocument: CadDocument
    PartSource: BoxSource
    OriginAxes: BoxOriginAxes


# a typed source record must still agree with the intact archive before it supplies dimensions
def CheckAttachDoc(Document: CadDocument) -> None:
    DocPair = NativeDocPair(Document)
    DataValue = DocPair[0].data if DocPair is not None else None
    if DataValue is None:
        raise ValueError("FreeCAD attached box has no exact retained document binding")
    ArchiveDoc = ReadNativeArc(
        DataValue,
        Document.source.path,
        None,
        None,
        0,
        False,
        False,
        True,
        None,
        DecodeNativeDoc,
    )
    if ArchiveDoc.to_json(indent=None) != Document.to_json(indent=None):
        raise ValueError(
            "FreeCAD attached box neutral owners disagree with its archive"
        )


# this intact source path is bounded to the measured legacy attachment inventory
def PlanAttachedBox(Document: CadDocument) -> AttachedBoxPlan:
    if (
        ReadBoxRelease(Document.source.application_version) != "0.21"
        or Document.brep is None
    ):
        raise ValueError("expected an intact FreeCAD 0.21 attached box source")
    CheckAttachDoc(Document)
    return AttachedBoxPlan(Document, ReadBoxSource(Document), ReadOriginAxes(Document))
