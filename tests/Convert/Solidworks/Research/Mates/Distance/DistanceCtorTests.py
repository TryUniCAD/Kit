from pytest import mark as MarkTest

from tests.Convert.Solidworks.Research.Mates.Distance.AssertDistGraph import (
    AssertDistGraph,
)
from tests.Convert.Solidworks.Research.Mates.Distance.MakeDistInput import MakeDistInput
from tests.Convert.Solidworks.Research.Mates.Distance.RunSdkDistance import (
    RunSdkDistance,
)


# every principal axis must preserve complete generated parent child and mate stream bytes through independent constructor processes
@MarkTest.parametrize("AxisValue", ("x", "y", "z"))
def TestDistCtor(AxisValue: str) -> None:
    BundleValue = MakeDistInput(AxisValue)
    AssertDistGraph(
        RunSdkDistance(BundleValue),
        RunSdkDistance(BundleValue, ModeValue="reference"),
        0.071375,
    )
