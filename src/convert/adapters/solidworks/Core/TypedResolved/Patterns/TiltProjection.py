from dataclasses import dataclass as DataClass

from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordParameter import Parameter
from interchange.geometry.Models.Selection import Selection
from interchange.geometry.Models.SupportPlane import SupportPlane


# projecting a constrained datum requires its two feature definitions and their owned public records together
@DataClass(frozen=True, slots=True)
class TiltProjection:
    HingeValue: FeatureStep
    PlaneValue: FeatureStep
    SupportValue: SupportPlane
    PicksValue: tuple[Selection, ...]
    OffsetValue: Parameter
