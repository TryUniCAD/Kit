from dataclasses import replace as ReplaceValue
from math import isfinite as IsFinite
from typing import Literal

from convert.adapters.base.GetDocumentCaps import GetDocumentCaps
from convert.adapters.solidworks.Archive.Construction.BodyNames.AnchorPartInput import (
    AnchorPartInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.Materials.PartMatIntent import (
    PartMatIntent,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectRectDims import (
    ProjectRectDims,
)
from convert.adapters.solidworks.Archive.Construction.Presentation.MakeModelVisual import (
    KModelTint,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.RectDimInput import (
    RectDimInput,
)
from convert.adapters.solidworks.Core.Preparation.CheckPlainScope import CheckPlainScope
from convert.adapters.solidworks.Core.Preparation.PartCaps import KPartWriteCaps
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Models.DocumentWalk import WalkDocuments
from interchange.document.Validation.DocumentValidate import AssertValid
from interchange.Enums.EnumDocument import Capability

# the physical assignment retains the catalog stem declared by the model
KMatCatalog = "solidworks_material_catalog"

# the declared origin constraint carries meaning independent of the contour position
KMatAnchor = "solidworks_origin_anchor"


# an explicit material request enters its own preparation route before body import
def IsPhysicalMat(DocumentValue: CadDocument) -> bool:
    return (
        DocumentValue.assembly is None
        and DocumentValue.DrawingValue is None
        and KMatCatalog in DocumentValue.metadata
    )


# other native writers must continue refusing typed material they cannot represent
def CanWriteMatDoc(DocumentValue: CadDocument) -> bool:
    return IsPhysicalMat(DocumentValue) or not any(
        PartValue.materials for PartValue in WalkDocuments(DocumentValue)
    )


# the declared corner or center must occupy the origin and own the sketch dimensions
def MakeMatAnchor(PlanValue: BlindPlan, KindValue: str) -> AnchorPartInput:
    LeftValue, BottomValue = PlanValue.VerticesValue[0]
    RightValue, TopValue = PlanValue.VerticesValue[2]
    AnchorKind: Literal["corner", "center"]
    if KindValue == "corner" and (LeftValue, BottomValue) == (0.0, 0.0):
        AnchorKind = "corner"
    elif KindValue == "center" and (LeftValue, BottomValue) == (-RightValue, -TopValue):
        AnchorKind = "center"
    else:
        raise ValueError(
            "material requires a declared rectangle anchor at the model origin"
        )
    WidthValue, HeightValue = PlanValue.WidthValue, PlanValue.HeightValue
    Dimensions = RectDimInput(
        (LeftValue + WidthValue / 2, BottomValue - 0.3 * HeightValue),
        (RightValue + 0.3 * WidthValue, BottomValue + HeightValue / 2),
        False,
        0,
        False,
    )
    return AnchorPartInput(AnchorKind, Dimensions)


# accept only modeled physical ownership and the default presentation that the shared cold archive emits
def PlanMatPart(
    DocumentValue: CadDocument,
) -> tuple[BlindPlan, AnchorPartInput, PartMatIntent]:
    CheckPlainScope(DocumentValue)
    AssertValid(DocumentValue)
    ModelValues = DocumentValue.metadata
    CatalogValue = ModelValues.get(KMatCatalog)
    KindValue = ModelValues.get(KMatAnchor)
    if (
        set(ModelValues) != {"name", KMatCatalog, KMatAnchor}
        or not isinstance(CatalogValue, str)
        or not isinstance(KindValue, str)
        or not GetDocumentCaps(DocumentValue)
        <= KPartWriteCaps | {Capability.KMaterials}
        or len(DocumentValue.materials) != 1
        or len(DocumentValue.bodies) != 1
    ):
        raise ValueError(
            "physical material requires one named assignment and explicit origin intent"
        )
    (BodyValue,) = DocumentValue.bodies
    (MaterialValue,) = DocumentValue.materials
    DefaultColor = tuple(
        ((KModelTint >> ShiftValue) & 255) / 255 for ShiftValue in (0, 8, 16)
    ) + (1.0,)
    if (
        BodyValue.material_id != MaterialValue.id
        or MaterialValue.ColorValue != DefaultColor
    ):
        raise ValueError(
            "physical material must belong to the sole result with default presentation"
        )
    GeometryValue = ReplaceValue(
        DocumentValue,
        bodies=(ReplaceValue(BodyValue, material_id=None),),
        materials=(),
        metadata={"name": ModelValues["name"]},
        capabilities=DocumentValue.capabilities - {Capability.KMaterials},
    )
    PlanValue = ProjectRectDims(GeometryValue)
    if (
        DocumentValue.units != "mm"
        or PlanValue.PlaneName != "Front Plane"
        or PlanValue.ConfigName != "Default"
    ):
        raise ValueError(
            "physical material requires the ordinary front millimetre part configuration"
        )
    MassValue = (
        PlanValue.WidthValue
        * PlanValue.HeightValue
        * PlanValue.DepthValue
        * MaterialValue.Density
    )
    if not IsFinite(MassValue) or MassValue <= 0:
        raise ValueError("physical material and boss geometry exceed finite mass")
    return (
        PlanValue,
        MakeMatAnchor(PlanValue, KindValue),
        PartMatIntent(CatalogValue, MaterialValue.name, float(MaterialValue.Density)),
    )
