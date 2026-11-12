from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Models.CheckInteger import CheckInteger


@MakeDataClass(frozen=True, slots=True)
class SketchLink:
    Primary: int
    Secondary: int
    Sense: int
    EnumA: int
    EnumB: int

    def __post_init__(self) -> None:
        CheckInteger(self.Primary, "sketch primary identity")
        CheckInteger(
            self.Secondary, "sketch secondary identity", Lower=0, Upper=(1 << 64) - 1
        )
        CheckInteger(self.Sense, "directed sketch sense", Lower=0, Upper=1)
        CheckInteger(self.EnumA, "sketch first enumeration")
        CheckInteger(self.EnumB, "sketch second enumeration")
