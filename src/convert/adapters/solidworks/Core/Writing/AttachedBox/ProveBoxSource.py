from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.freecad.Native import ArchiveMembers, LoadNative
from convert.adapters.freecad.Replay.NativeDocPair import NativeDocPair
from convert.adapters.registry.NativeWrite import CheckNative
from convert.adapters.solidworks.Core.Preparation.FreecadBox.PlanAttachedBox import (
    PlanAttachedBox,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.ProjectBoxAxes import (
    ProjectBoxAxes,
)
from convert.adapters.solidworks.Core.Writing.AttachedBox.BoxAuditData import (
    BoxAuditData,
)
from convert.adapters.solidworks.Core.Writing.AttachedBox.BoxProof import BoxProof
from convert.adapters.solidworks.Core.Writing.AttachedBox.BoxSourceCaps import (
    KBoxEvidenceCaps,
    KBoxSemanticCaps,
)
from convert.adapters.solidworks.Core.Writing.AttachedBox.ReadBoxShapes import (
    ReadBoxShapes,
)
from interchange.document.Models.DocumentModel import CadDocument


# source only data may be excluded from native transfer only after an intact independent proof
def ProveBoxSource(Document: CadDocument) -> BoxProof:
    PlanValue = PlanAttachedBox(Document)
    BoxValue = PlanValue.PartSource
    _ = ProjectBoxAxes(PlanValue.OriginAxes)
    CheckNative(BoxValue.ModelValue)
    if GetDocumentCaps(Document) != KBoxSemanticCaps | KBoxEvidenceCaps:
        raise ValueError(
            "attached FreeCAD source has an unrepresented functional capability"
        )
    SourcePair = NativeDocPair(Document)
    if SourcePair is None or SourcePair[0].data is None:
        raise ValueError("attached FreeCAD source lacks its authenticated archive pair")
    try:
        SourceArchive = LoadNative(SourcePair[0].data)
        Shapes = ReadBoxShapes(Document, SourceArchive, BoxValue)
        Archive, Members = ArchiveMembers(SourcePair[0].data)
        with Archive:
            if set(Members) != {
                "Document.xml",
                *(str(Value["member"]) for Value in Shapes),
            }:
                raise ValueError(
                    "FreeCAD attached box has other source archive members"
                )
    except (KeyError, TypeError, OverflowError) as ErrorInfo:
        raise ValueError(
            "attached FreeCAD source has a malformed shape owner"
        ) from ErrorInfo
    if {Payload.id for Payload in Document.brep_payloads} != {
        *(Payload.id for Payload in SourcePair),
        *(str(Value["id"]) for Value in Shapes),
    }:
        raise ValueError("attached FreeCAD source has unaccounted native payloads")
    return BoxProof(
        PlanValue, BoxAuditData(PlanValue, SourcePair, Shapes), KBoxSemanticCaps
    )
