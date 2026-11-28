from dataclasses import dataclass as DataClass


# feature stamps must come from an explicit qualified release target rather than a captured source feature
@DataClass(frozen=True, slots=True)
class FeatureTarget:
    DateCode: int
    ParasolidVersion: int
    FileVersion: int = 19000
    ServicePack: int = 5
    SubservicePack: int = 2

    # unsupported releases and out of range provenance must fail before any feature graph is initialized
    def __post_init__(self) -> None:
        if type(self.FileVersion) is not int or self.FileVersion != 19000:
            raise ValueError(
                "fresh feature construction requires archive version 19000"
            )
        if type(self.DateCode) is not int or not 0 <= self.DateCode <= 0x7FFFFFFF:
            raise ValueError("feature date code must fit a nonnegative signed integer")
        if (
            type(self.ParasolidVersion) is not int
            or not 0 < self.ParasolidVersion <= 0x7FFFFFFF
        ):
            raise ValueError(
                "feature kernel version must be an explicit positive signed integer"
            )
        if any(
            type(Value) is not int or not 0 <= Value <= 255
            for Value in (self.ServicePack, self.SubservicePack)
        ):
            raise ValueError("feature service pack values must fit unsigned bytes")
