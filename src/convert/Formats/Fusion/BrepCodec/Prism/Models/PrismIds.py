from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.BrepCodec.Models.CheckInteger import CheckInteger
from convert.Formats.Fusion.BrepCodec.Prism.PrismLayout import KFirstAttribute


# saved edits allocate topology identities that must survive typed history reconstruction
@MakeDataClass(frozen=True, slots=True)
class PrismIds:
    Entries: tuple[tuple[int, int], ...] = ()

    # invalid identity assignments must fail before they can replace body ownership or topology fields
    def __post_init__(self) -> None:
        if len({Index for Index, _ in self.Entries}) != len(self.Entries):
            raise ValueError("Prism entity identity owners must be distinct")
        for Index, Value in self.Entries:
            CheckInteger(
                Index, "prism entity ordinal", Lower=0, Upper=KFirstAttribute - 1
            )
            CheckInteger(Value, "prism entity identity", Lower=-1, Upper=(1 << 63) - 1)
            if Index == 1:
                raise ValueError("Prism body identity belongs to its body key")
