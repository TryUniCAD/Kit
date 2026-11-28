from dataclasses import dataclass as MakeDataClass

from interchange.geometry.Models.Transform import Transform


# an origin axis owns a placed carrier and stored model visibility without an authored extent
@MakeDataClass(frozen=True, slots=True)
class BoxOriginAxis:
    RecordId: str
    RoleName: str
    LabelValue: str
    FrameValue: Transform
    RecordShown: bool


# the separate origin record controls an ordered set of independently selectable axes
@MakeDataClass(frozen=True, slots=True)
class BoxOriginAxes:
    OriginId: str
    OriginLabel: str
    RecordShown: bool
    AxisValues: tuple[BoxOriginAxis, ...]
