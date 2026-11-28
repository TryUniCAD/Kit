from pytest import mark as MarkTest

from tests.Convert.Solidworks.Research.Mates.Construction.AssertSdkMate import (
    AssertSdkMate,
)
from tests.Convert.Solidworks.Research.Mates.Construction.MakeSdkMate import MakeSdkMate
from tests.Convert.Solidworks.Research.Mates.Construction.RunSdkMate import RunSdkMate


# all principal supports and distinct contours must survive independent composer and sdk processes with identical native artifacts
@MarkTest.parametrize("KindValue", ("coincident", "parallel"))
@MarkTest.parametrize("AxisValue", ("x", "y", "z"))
def TestSdkMates(KindValue: str, AxisValue: str) -> None:
    BundleValue = MakeSdkMate(KindValue, AxisValue)
    AssertSdkMate(
        RunSdkMate(BundleValue), RunSdkMate(BundleValue, ModeValue="reference")
    )
