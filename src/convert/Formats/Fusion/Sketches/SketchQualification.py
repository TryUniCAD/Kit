from dataclasses import replace as Replace

from convert.Formats.Fusion.HistoryRef import ReadNativeRef
from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.Sketches.SketchPlacement import KSketchFeature
from interchange.Features.FeatureStep import FeatureStep
from convert.Formats.Fusion.Sketches.SketchRuleIds import ReadSketchRules
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.geometry.Models.Sketch import Sketch


# native relation membership must account for every retained rule before promoting a timeline sketch
def HasSketchRules(BulkData: bytes, RootSpan: RecordSpan, SketchValue: Sketch) -> bool:
    try:
        Geometric, Dimensions = ReadSketchRules(BulkData, RootSpan, RequirePlain=True)
    except ValueError:
        return False
    return tuple(
        Relation.provenance.native_id if Relation.provenance is not None else ""
        for Relation in SketchValue.constraints
    ) == tuple(str(Identity) for Identity in Geometric + Dimensions)


# an operation using a sketch cannot become the reference step that originally created it
def IsSketchOwner(
    StepValue: FeatureStep, RootSpan: RecordSpan | None, BulkData: bytes
) -> bool:
    Origin = StepValue.provenance
    return (
        RootSpan is not None
        and StepValue.kind == FeatureKind.KNative
        and StepValue.definition is None
        and StepValue.attributes.get("fusion.state_known") is True
        and Origin is not None
        and Origin.adapter == "fusion.f3d"
        and any(Value.record_kind == KSketchFeature for Value in Origin.spans)
        and Origin.native_id
        == str(
            ReadNativeRef(
                MetaCursor(BulkData[RootSpan.EndOffset - 15 : RootSpan.EndOffset - 4])
            )
        )
    )


# only sketches with complete reciprocal membership and a resolved support may become portable reference steps
def QualifySketches(
    Document: CadDocument, BulkData: bytes, Spans: tuple[RecordSpan, ...]
) -> CadDocument:
    Roots = {str(Record.ObjectId): Record for Record in Spans if Record.IsPrimary}
    Supports = {
        Plane.id
        for Plane in Document.support_planes
        if Plane.attributes.get("fusion.native_support_resolved") is True
    }
    Qualified = {
        SketchValue.id: RootSpan
        for SketchValue in Document.sketches
        if SketchValue.provenance is not None
        and SketchValue.attributes.get("fusion.geometry_child_ids")
        and SketchValue.support_plane_id in Supports
        and not any(
            Entity.attributes.get("fusion.geometry_is_projected")
            for Entity in SketchValue.entities
        )
        and (RootSpan := Roots.get(SketchValue.provenance.native_id)) is not None
        and HasSketchRules(BulkData, RootSpan, SketchValue)
    }
    if not Qualified:
        return Document
    return Replace(
        Document,
        sketches=tuple(
            (
                Replace(
                    SketchValue,
                    attributes=FreezeMapping(
                        {**SketchValue.attributes, "fusion.geometry_partial": False}
                    ),
                )
                if SketchValue.id in Qualified
                else SketchValue
            )
            for SketchValue in Document.sketches
        ),
        feature_timeline=tuple(
            (
                Replace(StepValue, kind=FeatureKind.KReference)
                if IsSketchOwner(
                    StepValue, Qualified.get(StepValue.sketch_id or ""), BulkData
                )
                else StepValue
            )
            for StepValue in Document.feature_timeline
        ),
    )
