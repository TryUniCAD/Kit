from interchange.geometry.Models.Transform import Transform
from tests.Convert.Integration.Fusion.DualSide.DualCase import DualCase
from tests.Convert.Integration.Fusion.DualSide.ReadDualCases import ReadDualCases


# the decided xy admission corpus excludes separately unqualified placement frames
def ReadAdmitCases() -> tuple[DualCase, ...]:
    return tuple(
        Sample
        for Sample in ReadDualCases()
        if Sample.Frame == Transform()
        and (Sample.FirstTaper != 0 or Sample.SecondTaper != 0)
    )
