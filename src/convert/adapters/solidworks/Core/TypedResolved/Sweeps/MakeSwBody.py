from dataclasses import replace as ReplaceValue

from convert.Geometry.SweptTube.QuarterMetric import MeasureQuarter
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.ReadSwResult import (
    SwSavedBody,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.SwReadGraph import (
    SwReadGraph,
)
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordTopology import TopologyCounts


# native solids expose their physical topology separately from neutral periodic seam anchors
def MakeSwBody(
    StateValue: SwReadGraph,
    FeatureValue: FeatureStep,
    IncludeBrep: bool,
    SavedBody: SwSavedBody,
) -> tuple[DesignBody, BrepModel | None]:
    if IncludeBrep is not (SavedBody.ModelValue is not None):
        raise ValueError("saved sweep result differs from the requested geometry mode")
    return BindSwBody(StateValue, MakeSwMeasure(StateValue, FeatureValue), SavedBody)


# cold and saved projections share physical measurements for the same verified profile
def MakeSwMeasure(StateValue: SwReadGraph, FeatureValue: FeatureStep) -> DesignBody:
    SectionRadius = StateValue.SectionValue.CurveValue.Radius * 1000.0
    PathRadius = StateValue.PathValue.CurveValue.Radius * 1000.0
    MeasureValue = MeasureQuarter(SectionRadius, PathRadius)
    BodyId = f"{FeatureValue.id}:body"
    return DesignBody(
        BodyId,
        FeatureValue.name,
        FeatureValue.id,
        topology=TopologyCounts(
            solid_count=1,
            shell_count=1,
            face_count=3,
            edge_count=2,
            vertex_count=0,
            volume=MeasureValue.VolumeValue,
            surface_area=MeasureValue.AreaValue,
            bounding_box=MeasureValue.BoundsValue,
            valid=True,
        ),
        provenance=FeatureValue.provenance,
        attributes={
            "center_of_mass_mm": (
                MeasureValue.CenterValue.x,
                MeasureValue.CenterValue.y,
                MeasureValue.CenterValue.z,
            ),
            "mass_kg": RequireScalar(StateValue.DensityValue.FieldsValue.get("f58"))
            * MeasureValue.VolumeValue
            * 1e-9,
        },
    )


# the solved body retains its actual kernel label and live atom provenance
def BindSwBody(
    StateValue: SwReadGraph,
    BodyValue: DesignBody,
    SavedBody: SwSavedBody,
) -> tuple[DesignBody, BrepModel | None]:
    AtomValue = SavedBody.AtomValue
    BodyId = str(AtomValue.FieldsValue["f140"])
    ResultValue = ReplaceValue(
        BodyValue,
        name=SavedBody.NameValue,
        provenance=TypedProvenance(
            NativeNodeSpan(StateValue.LinkValue, AtomValue), BodyId
        ),
        attributes=dict(BodyValue.attributes)
        | {
            "native_atom_id": BodyId,
            "native_rgb": SavedBody.ColorValue,
            "native_translucency": SavedBody.Translucency,
        },
    )
    ModelValue = SavedBody.ModelValue
    if ModelValue is None:
        return ResultValue, None
    (SolidValue,) = ModelValue.bodies
    return ResultValue, ReplaceValue(
        ModelValue,
        bodies=(ReplaceValue(SolidValue, design_body_id=ResultValue.id),),
    )
