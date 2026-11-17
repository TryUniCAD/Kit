from __future__ import annotations

from typing import cast as CastValue

from pytest import raises as Raises

from tests.Convert.Solidworks.Research.FreshPartRunner import RunFreshPart
from tests.Convert.Solidworks.Research.Revolve.RevolveInput import MakeRevolve


# unsupported contours fail before an emitted file can omit the requested axis intent
def TestCrossedAxis() -> None:
    Request = MakeRevolve("z", "axis intersects contour", 125.0, False)
    Document = CastValue(dict[str, object], Request["document"])
    Document.update(axis_start_m=[0.02, -0.033], axis_end_m=[0.02, 0.041])
    with Raises(AssertionError, match="construction axis must be an upward line"):
        RunFreshPart(Request)
