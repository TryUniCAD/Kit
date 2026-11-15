from collections.abc import Sequence

from interchange.geometry.models.Sketch import Sketch


def ProfileInputs(Sketches: Sequence[Sketch]) -> set[str]:
    Profiles = set[str]()
    for SketchValue in Sketches:
        if SketchValue.suppressed or not SketchValue.closed_profile_entity_ids:
            continue
        Entities = {
            Entity.id for Entity in SketchValue.entities if not Entity.construction
        }
        if all(
            Group and set(Group) <= Entities
            for Group in SketchValue.closed_profile_entity_ids
        ):
            Profiles.add(SketchValue.id)
    return Profiles
