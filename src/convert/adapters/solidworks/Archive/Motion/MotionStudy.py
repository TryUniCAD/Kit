from dataclasses import dataclass as DataClass
from uuid import RFC_4122 as RfcVariant, UUID

# the observed english caption identifies the ordinary inactive study covered by this codec
KDefaultStudy = "Motion Study 1"


# each independently generated study needs a distinct explicit identity without calling a vendor session
@DataClass(frozen=True, slots=True)
class MotionStudy:
    IdentityValue: UUID
    NameValue: str

    # source studies outside the verified singleton caption and version four identity must refuse
    def __post_init__(self) -> None:
        if (
            type(self.IdentityValue) is not UUID
            or self.IdentityValue.variant != RfcVariant
            or self.IdentityValue.version != 4
            or self.NameValue != KDefaultStudy
        ):
            raise ValueError(
                "motion requires the ordinary default study with an explicit version four identity"
            )
