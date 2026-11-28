from collections.abc import Mapping

from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceFields import (
    RequireBox,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Validation.DocumentValidate import AssertValid
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureKinds import NativeFeature
from interchange.Features.FeatureStep import FeatureStep


# the source must carry one active primitive and no independent model domain to discard
def ReadBoxModel(
    DocumentValue: CadDocument,
) -> tuple[FeatureStep, NativeFeature, DesignBody, Mapping[str, object]]:
    AssertValid(DocumentValue)
    Source = DocumentValue.source
    RequireBox(
        Source.format_id == "freecad.fcstd"
        and Source.container_version == "1"
        and Source.attributes == {"freecad_schema_version": "4"}
        and str(DocumentValue.units) == "mm",
        "expected the measured FreeCAD schema-four primitive source",
    )
    RequireBox(
        set(DocumentValue.metadata) == {"freecad"}
        and not (
            DocumentValue.materials
            or DocumentValue.sketches
            or DocumentValue.selections
            or DocumentValue.assembly
            or DocumentValue.meshes
        ),
        "FreeCAD primitive includes another authored model domain",
    )
    RequireBox(
        len(DocumentValue.feature_timeline)
        == len(DocumentValue.bodies)
        == len(DocumentValue.configurations)
        == 1,
        "FreeCAD box translation requires one part body, one primitive and one active configuration",
    )
    (Feature,) = DocumentValue.feature_timeline
    (BodyValue,) = DocumentValue.bodies
    (Config,) = DocumentValue.configurations
    Definition = Feature.definition
    if type(Definition) is not NativeFeature:
        raise ValueError(
            "FreeCAD feature is outside the origin-fixed AdditiveBox profile"
        )
    RequireBox(
        Definition.format_id == "freecad.fcstd"
        and Definition.type_id == "PartDesign::AdditiveBox"
        and str(Feature.kind) == "primitive"
        and Feature.sketch_id is None
        and not (
            Feature.suppressed
            or Feature.input_feature_ids
            or Feature.selection_ids
            or Feature.configuration_states
            or Feature.operation
        ),
        "FreeCAD feature is outside the origin-fixed AdditiveBox profile",
    )
    RequireBox(
        BodyValue.final_feature_id == Feature.id
        and BodyValue.material_id is None
        and Config.active
        and Config.parent_id is None
        and not (
            Config.attributes or Config.overrides or Config.suppressed_feature_ids
        ),
        "FreeCAD box lost actual body, material or configuration ownership",
    )
    return (
        Feature,
        Definition,
        BodyValue,
        NativeRecord(DocumentValue.metadata["freecad"]),
    )
