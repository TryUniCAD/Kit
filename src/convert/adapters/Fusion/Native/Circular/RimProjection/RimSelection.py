from convert.adapters.Fusion.Native.Circular.RimPolicy.RimContext import RimContext
from interchange.geometry.Models.Selection import Selection, SelectPathElem


# the selected predecessor rim must survive driver edits without copied geometric dimensions
def RimSelection(Context: RimContext) -> Selection:
    return Selection(
        Context.SelectedRef.Identity,
        "Upper circular rim",
        (
            SelectPathElem("body", Context.Extrusion.BodyNode.Identity),
            SelectPathElem("feature", Context.Extrusion.Extrude.Identity, "upper_rim"),
        ),
        query={
            "entity_kind": "edge",
            "curve_kind": "circle",
            "position": "upper_rim",
            "source_feature_id": Context.Extrusion.Extrude.Identity,
        },
        attributes={
            "fusion.tag_groups": tuple(
                tuple(
                    {
                        "primary": "".join(chr(Value) for Value in TagValue.PrimaryId),
                        "operations": TagValue.OperationIds,
                        "secondary": TagValue.SecondaryId,
                        "approach": TagValue.ApproachId,
                    }
                    for TagValue in Group
                )
                for Group in Context.Recipe.Tags
            )
        },
    )
