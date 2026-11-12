from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Models.CheckInteger import CheckInteger


@MakeDataClass(frozen=True, slots=True)
class FeatureTag:
    Selector: int
    Label: str
    Operations: tuple[int, ...]

    def __post_init__(self) -> None:
        CheckInteger(self.Selector, "feature selector", Lower=0)
        if (
            not self.Label
            or not self.Label.isprintable()
            or len(self.Label.encode("utf-8")) > 255
        ):
            raise ValueError(
                "Fusion BRep feature label must fit a printable short string"
            )
        if type(self.Operations) is not tuple or not 1 <= len(self.Operations) <= 256:
            raise ValueError(
                "Fusion BRep feature tag requires one to 256 operation identities"
            )
        for Value in self.Operations:
            CheckInteger(Value, "operation identity", Lower=0)
