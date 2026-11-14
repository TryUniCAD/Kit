from interchange.document.models.DocumentModel import CadDocument
from interchange.document.models.DocumentWalk import WalkDocuments
from interchange.features.FeatureKinds import NativeFeature
from interchange.geometry.models.GeometryCurves import NativeGeometry


def CheckPortable(Document: CadDocument) -> None:
    for PartValue in WalkDocuments(Document):
        if PartValue.metadata.get("kit.research_read_status") == "unqualified":
            raise ValueError(
                "UnqualifiedResearch documents are not conversion-ready; "
                + "use kit decode or kit research for inspection"
            )
        for Feature in PartValue.FeatureTimeline:
            if isinstance(Feature.definition, NativeFeature):
                raise ValueError(
                    "NativeFeature records are not conversion-ready; "
                    + "use kit decode or kit research for inspection"
                )
        for Sketch in PartValue.Sketches:
            for Entity in Sketch.Entities:
                if isinstance(Entity.Geometry, NativeGeometry):
                    raise ValueError(
                        "NativeGeometry records are not conversion-ready; "
                        + "use kit decode or kit research for inspection"
                    )
