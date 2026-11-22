from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import (
    SetCfgStampMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.Imports.BindImportScene import (
    BindImportScene,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.System.Members.LightInput import (
    LightInput,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# scene members extend the actual shared configuration and header allocator
def AddCylLights(
    ChildValue: PartCandidate,
    LightValues: tuple[LightInput, ...],
    TargetValue: FeatureTarget,
) -> None:
    HeadersValue = ChildValue.HeaderValue.FieldsValue, ChildValue.TopHeader.FieldsValue
    StartIndex = FieldInt(HeadersValue[0], "f08")
    if StartIndex != FieldInt(HeadersValue[1], "f08"):
        raise ValueError(
            "concentric child scene requires consistent header identity cursors"
        )
    Allocator = PersistentIds(StartIndex)
    BindImportScene(ChildValue.SystemValue, LightValues, TargetValue, Allocator)
    SetCfgStampMut(ChildValue.CurrentConfig, Allocator)
    for HeaderValue in HeadersValue:
        HeaderValue["f08"] = Allocator.NextValue
