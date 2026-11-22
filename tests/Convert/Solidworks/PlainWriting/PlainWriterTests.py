from math import isclose as IsClose
from os import name as OsName
from typing import cast as CastValue

from tests.Convert.Solidworks.PlainWriting.RunPlainCase import RunPlainCase

# the independently measured three and six line profiles give different stream extents
KPlainCases = (
    ("Skew", 3, 12.75, 7658.7975),
    ("Step", 6, 18.625, 19822.77375),
)


# public placement requires full archive equality while readback retains its actual model and driver
def TestPlainWriter() -> None:
    Sizes: list[int] = []
    for RoleName, SideCount, DepthValue, VolumeValue in KPlainCases:
        ReportValue = RunPlainCase(RoleName)
        assert ReportValue["measurements_accepted"] == (2 if OsName == "nt" else 3)
        assert ReportValue["target_file_opens"] == (0 if OsName == "nt" else 1)
        Refusals = CastValue(list[str], ReportValue["refusals"])
        assert set(Refusals) == {
            "bad_build",
            "changed_model",
            "different_epoch",
            "different_locator",
            "failed_control",
            "missing_digests",
            "missing_receipt",
            "missing_reopen",
            "unclean_generated",
        }
        assert set(CastValue(list[str], ReportValue["retained_policy_refusals"])) == {
            "disconnected_loop",
            "overwrite_guard",
            "raw_extraction",
            "unknown_model_data",
            "unmodeled_configuration",
            "unnamed_stream",
            "unsupported_extension",
        }
        assert ReportValue["native_capabilities"] == [
            "body_structure",
            "configurations",
            "editable_sketches",
            "parameters",
            "parametric_history",
            "support_planes",
        ]
        CheckPlainRead(ReportValue, SideCount, DepthValue, VolumeValue)
        Sizes.append(CastValue(int, ReportValue["resolved_stream_bytes"]))
    assert 0 < Sizes[0] < Sizes[1]


# exact public readback must bind the recovered depth and solid to their typed feature
def CheckPlainRead(
    ReportValue: dict[str, object],
    SideCount: int,
    DepthValue: float,
    VolumeValue: float,
) -> None:
    Readback = CastValue(dict[str, object], ReportValue["readback"])
    assert Readback["tree_rows"] == Readback["linked_root_rows"] == 19
    assert Readback["line_count"] == SideCount
    NameValue, UnitValue, ActualDepth, IsDriving = CastValue(
        list[object], Readback["driving_dimension"]
    )
    assert (NameValue, UnitValue, IsDriving) == ("D1", "mm", True)
    assert IsClose(CastValue(float, ActualDepth), DepthValue, rel_tol=0, abs_tol=1e-12)
    Geometry = CastValue(dict[str, object], ReportValue["default_geometry"])
    assert Geometry["topology"] == [1, 1, SideCount + 2, 3 * SideCount, 2 * SideCount]
    assert Geometry["body_feature_linked"] is True
    assert IsClose(CastValue(float, Geometry["volume_mm3"]), VolumeValue, rel_tol=1e-12)
