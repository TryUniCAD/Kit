from convert.adapters.solidworks.Archive.Construction.BodyScope.BindStockMut import (
    BindStockMut,
)
from convert.adapters.solidworks.Archive.Construction.Circles.Attachment.AddCylLights import (
    AddCylLights,
)
from convert.adapters.solidworks.Archive.Construction.Circles.Attachment.BindCylMarksMut import (
    BindCylMarksMut,
)
from convert.adapters.solidworks.Archive.Construction.Circles.Attachment.CheckCylLights import (
    CheckCylLights,
)
from convert.adapters.solidworks.Archive.Construction.Circles.Attachment.CheckFreshCyl import (
    CheckFreshCyl,
)
from convert.adapters.solidworks.Archive.Construction.Circles.Attachment.CylChild import (
    CylChild,
)
from convert.adapters.solidworks.Archive.Construction.Circles.Attachment.EmitCylChild import (
    EmitCylChild,
)
from convert.adapters.solidworks.Archive.Construction.Circles.Attachment.LogCylUpdateMut import (
    LogCylUpdateMut,
)
from convert.adapters.solidworks.Archive.Construction.Circles.Attachment.ReadAttCyl import (
    ReadAttCyl,
)
from convert.adapters.solidworks.Archive.Construction.Circles.RadialLabelIn import (
    RadialLabelIn,
)
from convert.adapters.solidworks.Archive.Construction.Part.Displays.Rendering.PartLookInput import (
    PartLookInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakeCirclePart import (
    MakeCirclePart,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CirclePlan import (
    CirclePlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import (
    DatumTime,
)
from convert.adapters.solidworks.Archive.Construction.System.Members.LightInput import (
    LightInput,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Attributes.BodyTrackIn import (
    BodyTrackIn,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.MakeCylTrans import (
    MakeCylTrans,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
)
from interchange.document.Models.DocumentModel import CadDocument


# a newly generated attached child derives its only live atom and partition from the same native circle and feature nodes
def MakeCylChild(
    DocumentValue: CadDocument,
    RecipeValue: PartBuildInput,
    LightValues: tuple[LightInput, ...],
    *,
    LabelValue: RadialLabelIn | None = None,
    LookValue: PartLookInput | None = None,
) -> CylChild:
    ChildValue = MakeCirclePart(DocumentValue, RecipeValue, LabelValue=LabelValue)
    PlanValue = ChildValue.PlanValue
    if (
        not isinstance(PlanValue, CirclePlan)
        or DocumentValue.units != "mm"
        or PlanValue.AxisValue != "z"
        or PlanValue.PlaneName != "Front Plane"
        or PlanValue.EndValue.ModeValue != "blind"
        or PlanValue.EndValue.IsReversed
    ):
        raise ValueError(
            "concentric attachment requires a forward blind Front circle part"
        )
    WrittenAt = RecipeValue.OutputValue.SavedAt
    HeaderValue = RecipeValue.HeaderValue
    if (HeaderValue.CreatedAt, HeaderValue.ModifiedAt, HeaderValue.UpdatedAt) != (
        WrittenAt,
    ) * 3:
        raise ValueError("concentric attachment requires one explicit fresh part event")
    CheckCylLights(PlanValue, RecipeValue, LightValues)
    Manager = CheckFreshCyl(ChildValue)
    SpanValue, ArcMarker = ReadAttCyl(ChildValue, PlanValue)
    BossValue = ChildValue.BossValue.FeatureValue
    AtomValue = BindStockMut(Manager, BossValue)
    Manager["fa8"] = ChildValue.ConfigValue.VersionValue
    BodyStamp, UpdateStamp = LogCylUpdateMut(ChildValue, WrittenAt)
    FeatureId = FieldInt(BossValue.FieldsValue, "f08")
    NativeValue = MakeCylTrans(
        SpanValue,
        BodyTrackIn(
            FeatureId,
            DatumTime(ChildValue.HeaderValue, FeatureId),
            ReadNodeName(BossValue),
            ArcMarker,
            FieldInt(AtomValue.FieldsValue, "f140"),
            BodyStamp,
            UpdateStamp,
        ),
    )
    BindCylMarksMut(ChildValue, AtomValue, NativeValue)
    AddCylLights(ChildValue, LightValues, RecipeValue.TargetValue)
    return CylChild(
        EmitCylChild(
            ChildValue, RecipeValue, NativeValue.BytesValue, LookValue=LookValue
        ),
        NativeValue.FaceTag,
    )
