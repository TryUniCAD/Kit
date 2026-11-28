from convert.adapters.solidworks.Assembly.PlanarMates.PlanarMate import PlanarMate
from interchange.assembly.AssemblyEnums import MateAlignment


# a perpendicular command without an internal alignment selection must preserve that unknown orientation instead of inventing aligned intent
def ReadMateAlign(PlanValue: PlanarMate) -> MateAlignment:
    if PlanValue.KindValue == "perpendicular":
        if PlanValue.AlignmentCode != 0:
            raise ValueError("perpendicular alignment is outside the measured mode")
        return MateAlignment.UNKNOWN
    return MateAlignment.ALIGNED
