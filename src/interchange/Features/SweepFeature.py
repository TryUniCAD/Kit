from dataclasses import dataclass as DataClass
from typing import cast as CastValue

from interchange.Features.FeatureContract import FeatureDef


# a standard sweep keeps its actual path sketch independent of the section sketch on the owning feature step
@DataClass(frozen=True, slots=True)
class SweepFeature(FeatureDef):
    PathSketchId: str

    # a missing path cannot be replaced by an inferred edge or a sampled curve
    def __post_init__(self) -> None:
        PathValue = CastValue(object, self.PathSketchId)
        if (
            not isinstance(PathValue, str)
            or not PathValue.strip()
            or "\x00" in PathValue
        ):
            raise ValueError("sweep path sketch id must be nonempty text")
