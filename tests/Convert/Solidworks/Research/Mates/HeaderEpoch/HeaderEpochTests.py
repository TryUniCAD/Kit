from pytest import mark as MarkTest
from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Mates.HeaderEpoch.MakeEpochProbe import (
    MakeEpochProbe,
)
from tests.Convert.Solidworks.Research.Mates.HeaderEpoch.RunEpochProbe import (
    RunEpochProbe,
)


# both header views must retain identical complete bundles and the actual first datum event across principal supports
@MarkTest.parametrize("AxisValue", ("x", "y", "z"))
@MarkTest.parametrize("CaseValue", ("absent", "empty", "authored"))
def TestHeaderEpoch(AxisValue: str, CaseValue: str) -> None:
    Reference = RunEpochProbe(
        MakeEpochProbe(AxisValue, CaseValue, "body", ModeValue="reference")
    )
    for ViewValue in ("body", "sdk"):
        Current = RunEpochProbe(MakeEpochProbe(AxisValue, CaseValue, ViewValue))
        assert Current["runtime_file_read_attempts"] == 0
        for FieldName in ("assembly", "child", "mate_stream", "readback"):
            assert Current[FieldName] == Reference[FieldName], FieldName
        Constructor = CastValue(dict[str, object], Current["constructor"])
        HeaderState = CastValue(dict[str, object], Constructor["header_epoch"])
        assert HeaderState["actual_log_identities_preserved"] is True
        Readback = CastValue(dict[str, object], Current["readback"])
        DrivingValue = CastValue(dict[str, object], Readback["driving_distance"])
        assert (
            DrivingValue["selected_datum_epochs"]
            == [1794700000 if CaseValue == "authored" else 2592000] * 2
        )
