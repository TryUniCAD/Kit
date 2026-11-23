from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.NativeSourceKey import KSourceFormatKey
from convert.adapters.solidworks.Core.Preparation.Equations.ReadEqSketch import (
    ReadEqSketch,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Readback.ReadTopDims import (
    ReadTopDims,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Sketch import Sketch
from interchange.Records.RecordTopology import TopologyCounts


# the independent body identity must come from the actual complete reconstructed solid and its archive atom
def RequireTopBody(Document: CadDocument) -> DesignBody:
    if (
        Document.source.format_id != KPartFormatId
        or Document.source.container_version != "4"
        or Document.metadata.get(KSourceFormatKey) != KPartFormatId
        or Document.assembly is not None
        or Document.DrawingValue is not None
        or Document.brep is None
        or Document.brep_payloads
        or Document.materials
        or Document.meshes
        or len(Document.bodies) != 1
    ):
        raise ValueError("SOLIDWORKS Top corner needs its full cache-free source")
    (BodyValue,) = Document.bodies
    OwnerValue = NativeRecord(
        BodyValue.attributes.get("solidworks.authored_output_name")
    )
    if (
        BodyValue.topology.solid_count != 1
        or OwnerValue.get("complete_brep_binding") is not True
        or OwnerValue.get("name_owner") != "authored_archive_atom"
        or OwnerValue.get("geometry_source") != "typed_parametric_history"
    ):
        raise ValueError("SOLIDWORKS Top corner lacks its authored body identity")
    return BodyValue


# only the actual source creator profile and external origin datum may enter the anchored body constructor
def ReadTopLineage(
    Timeline: tuple[FeatureStep, ...], BodyValue: DesignBody, SketchValue: Sketch
) -> tuple[FeatureStep, FeatureStep]:
    (BossValue,) = (
        Value for Value in Timeline if Value.id == BodyValue.final_feature_id
    )
    (ProfileValue,) = (
        Value for Value in Timeline if Value.id in BossValue.input_feature_ids
    )
    if (
        BossValue.kind != FeatureKind.KExtrusion
        or BossValue.operation != BooleanOp.KCreate
        or BossValue.input_feature_ids != (ProfileValue.id,)
        or BossValue.sketch_id != SketchValue.id
        or ProfileValue.sketch_id != SketchValue.id
        or ProfileValue.parameter_ids != SketchValue.parameter_ids
        or SketchValue.attributes.get("typed_origin_coincidence") is not True
        or SketchValue.attributes.get("typed_line_dimensions") is not True
    ):
        raise ValueError("SOLIDWORKS Top corner lacks its typed creator and origin")
    return BossValue, ProfileValue


# the construction view carries authored intent while its caller verifies the untouched original document
def ReadTopInput(Document: CadDocument, NameValue: str) -> CadDocument:
    BodyValue = RequireTopBody(Document)
    (SketchValue,) = Document.sketches
    (ConfigValue,) = Document.configurations
    (PlaneValue,) = (
        Value
        for Value in Document.support_planes
        if Value.id == SketchValue.support_plane_id
    )
    BossValue, ProfileValue = ReadTopLineage(
        Document.feature_timeline, BodyValue, SketchValue
    )
    FeatureValue, Parameters = ReadTopDims(
        Document.parameters, BossValue, ProfileValue, SketchValue.id
    )
    return ReplaceValue(
        Document,
        source=ReplaceValue(Document.source, attributes=FreezeMapping()),
        configurations=(ReplaceValue(ConfigValue, attributes=FreezeMapping()),),
        parameters=Parameters,
        support_planes=(
            ReplaceValue(PlaneValue, attributes=FreezeMapping(), provenance=None),
        ),
        sketches=(ReadEqSketch(SketchValue),),
        selections=(),
        feature_timeline=(FeatureValue,),
        bodies=(
            ReplaceValue(
                BodyValue,
                topology=TopologyCounts(),
                attributes=FreezeMapping(),
                provenance=None,
            ),
        ),
        brep=None,
        diagnostics=(),
        metadata=FreezeMapping({"name": NameValue}),
        capabilities=frozenset(),
    )
