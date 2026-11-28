from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep


# native bookkeeping does not justify discarding authored alternate extrusion references or dimensions
def ReadSourceEnd(FeatureValue: FeatureStep) -> ExtrudeFeature:
    Definition = FeatureValue.definition
    if type(Definition) is not ExtrudeFeature or FeatureValue.kind != "extrusion":
        raise ValueError("source operation lacks its actual extrusion definition")
    if (
        FeatureValue.suppressed
        or FeatureValue.configuration_states
        or any(
            getattr(Definition, NameValue) is not None
            for NameValue in (
                "offset",
                "second_offset",
                "draft_angle",
                "second_draft_angle",
            )
        )
        or Definition.up_to_reference
        or Definition.second_up_to_reference
    ):
        raise ValueError("source operation has unrepresented end or variant intent")
    return Definition
