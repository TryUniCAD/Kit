from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.Preparation.FreecadBox.LowerBoxModel import (
    MakeBoxNeutral,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Primitive.CheckStockShape import (
    ReadStockShape,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Primitive.ReadStockDims import (
    ReadStockDims,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Primitive.ReadStockPlace import (
    ReadStockPlace,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Primitive.ReadStockSource import (
    ReadStockSource,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Validation.DocumentValidate import AssertValid
from interchange.geometry.Models.SupportPlane import SupportPlane


# the selected stock must derive geometry from its own primitive inputs without changing its source graph
def PlanFcStock(
    Document: CadDocument, FeatureId: str, PartName: str, *, Placed: bool = False
) -> CadDocument:
    AssertValid(Document)
    ArchiveValue, OwnerValue, FeatureValue = ReadStockSource(Document, FeatureId)
    Length, Width, Height = ReadStockDims(Document.parameters, OwnerValue, FeatureValue)
    PoseValue = ReadStockPlace(OwnerValue, FeatureValue.name, Placed=Placed)
    if len(Document.configurations) != 1:
        raise ValueError("FreeCAD stock requires one actual configuration")
    (ConfigValue,) = Document.configurations
    if (
        not ConfigValue.active
        or ConfigValue.parent_id is not None
        or ConfigValue.overrides
        or ConfigValue.suppressed_feature_ids
        or ConfigValue.attributes
        or FeatureValue.configuration_states
    ):
        raise ValueError("FreeCAD stock requires an unmodified active configuration")
    Sizes = (
        RequireScalar(Length.value.value),
        RequireScalar(Width.value.value),
        RequireScalar(Height.value.value),
    )
    Origin = PoseValue.origin
    _ = ReadStockShape(
        Document,
        ArchiveValue,
        OwnerValue,
        FeatureId,
        Sizes,
        Minimum=(Origin.x, Origin.y, Origin.z),
        Placed=Placed,
    )
    BodyId = FeatureId + ":stock"
    if (
        Placed
        and len(Document.feature_timeline) == len(Document.bodies) == 1
        and Document.bodies[0].final_feature_id == FeatureId
    ):
        BodyId = Document.bodies[0].id
    return MakeBoxNeutral(
        Document,
        PartName,
        (Length.id, Width.id, Height.id),
        Sizes,
        (Length.name, Width.name, Height.name),
        FeatureValue.name,
        SourceFeature=FeatureValue,
        SourcePlane=SupportPlane(FeatureId + ":placement", "XY-plane", PoseValue),
        BodyId=BodyId,
    )
