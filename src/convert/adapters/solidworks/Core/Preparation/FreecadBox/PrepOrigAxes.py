from convert.adapters.freecad.BodyLineage.BoxNativeOwner import ReadBoxArchive
from convert.adapters.freecad.Native import NativeObjectA
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.PlanOriginBox import (
    PlanOriginBox,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.PrepareBoxAxes import (
    PrepareBoxAxes,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.ProjectBoxAxes import (
    ProjectBoxAxes,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadOriginAxes import (
    ReadOriginAxes,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from interchange.document.Models.DocumentModel import CadDocument


# the original box and its selectable origin axes must derive from the same strict source archive
def PrepOrigAxes(DocumentValue: CadDocument, PathValue: str) -> PartCandidate:
    SourceValue = PlanOriginBox(DocumentValue).PartSource
    Metadata = NativeRecord(DocumentValue.metadata["freecad"])
    Archive = ReadBoxArchive(DocumentValue)
    if NativeRows(Metadata["objects"]) != tuple(
        NativeObjectA(Value) for Value in Archive.objects
    ):
        raise ValueError("FreeCAD origin datum owners disagree with the source archive")
    AxesValue = ProjectBoxAxes(ReadOriginAxes(DocumentValue, CheckPlanes=True))
    return PrepareBoxAxes(
        SourceValue.ModelValue,
        PathValue,
        SourceValue.CreationEpoch,
        SourceValue.PropertiesValue,
        AxesValue,
        TopAttached=False,
        UnitsValue=SourceValue.UnitsValue,
    )
