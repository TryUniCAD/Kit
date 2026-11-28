from convert.adapters.solidworks.Core.Writing.Measured.ReadMeasNum import ReadMeasNum
from convert.adapters.solidworks.Core.Writing.Sweeps.HasCleanSwCode import (
    HasCleanSwCode,
)


# both controls must observe the same intact input and a healthy native solid
def CheckSwControl(Phase: dict[str, object], Label: str, InputHash: str) -> None:
    if (
        Phase.get("phase") != Label
        or Phase.get("slot") is not None
        or Phase.get("source") != InputHash
        or Phase.get("result") != InputHash
        or not HasCleanSwCode(Phase.get("open_status"))
        or Phase.get("rebuilt") is not True
        or type(Phase.get("solid_count")) is not int
        or Phase["solid_count"] != 1
    ):
        raise ValueError("sweep measurement requires both healthy bracket controls")
    _ = ReadMeasNum(Phase.get("volume_m3"))
    _ = ReadMeasNum(Phase.get("area_m2"))
