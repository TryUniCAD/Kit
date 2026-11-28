from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.BodyNameGraph import (
    BodyNameGraph,
)
from convert.adapters.solidworks.Core.TypedResolved.Equations.CheckEqConfig import (
    CheckEqConfig,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckPrismRels import (
    CheckPrismRels,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.CheckSingleBoss import (
    CheckSingleBoss,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.BindPrismCreate import (
    BindPrismCreate,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.SavedScope.CheckSavedBoss import (
    CheckSavedBoss,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.SavedScope.CheckSavedFaces import (
    CheckSavedFaces,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.SavedScope.CheckSaveSketch import (
    CheckSaveSketch,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.ReadExtrude import ReadExtrude
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureStep import FeatureStep


# saved scope must use the real active directory row and relation state
def CheckSaveConfig(
    Document: CadDocument, Archive: SldprtArchive, LinkValue: NativeLink
) -> str:
    (Selected,) = Document.configurations
    Manager = ReadCmgrMut(
        Archive.require("Contents/CMgr"), LinkValue.ConfigValue.VersionValue
    )
    Report = Manager.ReportValue
    if (
        not Selected.active
        or Selected.id != "sldprt:configuration:0"
        or Selected.parent_id is not None
        or Selected.overrides
        or Selected.suppressed_feature_ids
        or not Report.get("completed")
        or Report.get("missing_schemas")
        or Report.get("provisional_schemas")
    ):
        raise ValueError(
            "SOLIDWORKS saved first boss requires its complete active configuration"
        )
    CheckEqConfig(Manager.RootValue, Selected.name)
    CheckPrismRels(LinkValue.ConfigValue.RootValue)
    return Selected.name


# projected driver and profile identities must alias the actual persistent feature owners
def ReadSaveSteps(
    Document: CadDocument, LinkValue: NativeLink, OwnerValue: ExtrudeOwner
) -> tuple[FeatureStep, FeatureStep]:
    BossValue, ProfileValue = OwnerValue.NodeValue, OwnerValue.ProfileValue
    StepId = f"sldprt:feature:{NativeNodeId(BossValue)}"
    ProfileId = f"sldprt:feature:{NativeNodeId(ProfileValue)}"
    Steps = {StepValue.id: StepValue for StepValue in Document.feature_timeline}
    Creator, Profile = Steps[StepId], Steps[ProfileId]
    if (
        Creator.input_feature_ids != (ProfileId,)
        or Creator.sketch_id != Profile.sketch_id
        or Creator.name != ReadNativeName(BossValue)
        or Profile.name != ReadNativeName(ProfileValue)
        or Creator.attributes.get("typed_archive_owner")
        != NativeNodeSpan(LinkValue, BossValue)
        or Profile.attributes.get("typed_archive_owner")
        != NativeNodeSpan(LinkValue, ProfileValue)
    ):
        raise ValueError(
            "SOLIDWORKS saved first boss lost its projected feature owners"
        )
    Depth = OwnerValue.RequireDepth().DepthValue
    (Parameter,) = (
        Value for Value in Document.parameters if Value.id in Creator.parameter_ids
    )
    if (
        Depth.name != "D1"
        or Parameter.name != Depth.name
        or Parameter.value.value != Depth.value_mm
        or Parameter.attributes.get("typed_archive_owner") != Depth.TypedOwner
        or len(Document.parameters) != 3
    ):
        raise ValueError("SOLIDWORKS saved first boss lacks its actual active depth")
    return Creator, Profile


# only the saved body naming proof can admit the same result into the scoped feature projection
def ReadSaveScope(
    Document: CadDocument, Archive: SldprtArchive, GraphValue: BodyNameGraph
) -> CadDocument:
    LinkValue = GraphValue.LinkValue
    Features = IndexFeatures(LinkValue)
    BossValue = Features[GraphValue.FeatureId]
    if BossValue.FieldsValue.get("f544") != 1 or GraphValue.IsAuthored:
        return Document
    CheckSingleBoss(Features, "moExtrusion_c")
    if (
        {
            StepValue.attributes.get("native_object_id")
            for StepValue in Document.feature_timeline
        }
        != set(Features)
        or len(Document.feature_timeline) != len(Features)
        or any(StepValue.suppressed for StepValue in Document.feature_timeline)
    ):
        raise ValueError(
            "SOLIDWORKS saved first boss requires its complete active history"
        )
    ConfigName = CheckSaveConfig(Document, Archive, LinkValue)
    OwnerValue = ReadExtrude(LinkValue, BossValue, Features)
    CheckSavedBoss(OwnerValue, GraphValue)
    Creator, Profile = ReadSaveSteps(Document, LinkValue, OwnerValue)
    LoopValue = CheckSaveSketch(Document, LinkValue, OwnerValue, Profile, Features)
    CheckSavedFaces(Archive, LinkValue, BossValue, LoopValue, ConfigName)
    Projected = BindPrismCreate(Document, Creator, FirstScope=True)
    Projected.assert_valid()
    return Projected


# unsupported saved geometry and history retain their established public projection
def WithSavedScope(
    Document: CadDocument, Archive: SldprtArchive, GraphValue: BodyNameGraph
) -> CadDocument:
    try:
        return ReadSaveScope(Document, Archive, GraphValue)
    except (ValueError, TypeError, KeyError):
        return Document
