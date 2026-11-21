from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Configuration.Events.ConfigEvent import (
    ConfigEvent,
)


# actual manager and active configuration owners must not share an inferred event merely because observed times coincide
@DataClass(frozen=True, slots=True)
class CmgrEvents:
    ManagerValue: ConfigEvent
    ActiveValue: ConfigEvent

    # each distinct native owner must have its own explicit semantic event input
    def __post_init__(self) -> None:
        if (
            type(self.ManagerValue) is not ConfigEvent
            or type(self.ActiveValue) is not ConfigEvent
        ):
            raise ValueError(
                "manager events require two typed configuration feature events"
            )
