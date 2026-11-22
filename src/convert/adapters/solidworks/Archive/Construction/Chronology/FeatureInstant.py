from dataclasses import dataclass as DataClass


# source feature moments need subsecond precision independently from whole second revision events
@DataClass(frozen=True, slots=True)
class FeatureInstant:
    SecondsValue: int
    FractionTicks: int

    # unsupported precision or signed epoch values must fail before native time words are derived
    def __post_init__(self) -> None:
        if (
            type(self.SecondsValue) is not int
            or not 0 <= self.SecondsValue <= 0xFFFFFFFF
            or type(self.FractionTicks) is not int
            or not 0 <= self.FractionTicks < 10_000_000
        ):
            raise ValueError(
                "feature instant requires wall seconds and fractional filetime ticks"
            )
