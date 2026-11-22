from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.Offsets.FaceOffset import FaceOffset


# a face pick must resolve through the selected body rather than merely name a face elsewhere
def OffsetTopoErrs(Feature: FeatureStep, Document: CadDocument) -> tuple[str, ...]:
    Definition = Feature.definition
    if not isinstance(Definition, FaceOffset):
        return ()
    Model = Document.brep
    Selected = next(
        (
            Value
            for Value in Document.selections
            if Value.id == Definition.FaceSelectionId
        ),
        None,
    )
    if Model is None or Selected is None or len(Selected.path) != 2:
        return (f"face offset {Feature.id} requires resolved face topology",)
    RegionIds = {
        Identity
        for BodyValue in Model.bodies
        if BodyValue.design_body_id == Definition.TargetBodyId
        for Identity in BodyValue.region_ids
    }
    ShellUseIds = {
        Identity
        for Region in Model.regions
        if Region.id in RegionIds
        for Identity in Region.shell_use_ids
    }
    ShellIds = {Value.shell_id for Value in Model.shell_uses if Value.id in ShellUseIds}
    FaceUseIds = {
        Identity
        for Shell in Model.shells
        if Shell.id in ShellIds
        for Identity in Shell.face_use_ids
    }
    FaceIds = {Value.face_id for Value in Model.face_uses if Value.id in FaceUseIds}
    if Selected.path[1].entity_id not in FaceIds.intersection(
        Value.id for Value in Model.faces
    ):
        return (f"face offset {Feature.id} selects a missing face or another body",)
    return ()
