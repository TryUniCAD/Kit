from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Construction.Part.AssertPartBytes import (
    AssertPartBytes,
)


# ownership checks must prove retained editable dimension and linked graph identities while keeping native acceptance explicitly unclaimed
def AssertPartFlow(
    BuildValue: dict[str, object],
    Prepared: dict[str, object],
    Counterpart: dict[str, object],
    RejectionCount: int = 12,
) -> int:
    AssertPartBytes(BuildValue, Prepared, Counterpart)
    assert (
        BuildValue["feature_count"]
        == Prepared["feature_count"]
        == Counterpart["feature_count"]
        == 19
    )
    assert BuildValue["configuration_count"] == 1
    Dimensions = CastValue(list[int], BuildValue["dimension_ids"])
    assert len(Dimensions) == len(set(Dimensions)) == 5
    assert BuildValue["parameter_names"] == ["D1", "D2", "D3", "D4", "D19"]
    for NameValue in (
        "actual_model_alias",
        "actual_active_configuration",
        "actual_profile_dependency",
        "actual_self_file_alias",
        "actual_manager_header",
        "plain_archive_nodes",
        "retained_from_dimension",
    ):
        assert BuildValue[NameValue] is True
    assert (
        Prepared["actual_profile_dependency"]
        is Prepared["actual_support_owner"]
        is Prepared["actual_configuration_map_aliases"]
        is True
    )
    Geometry = CastValue(dict[str, object], Prepared["geometry"])
    PointCount = len(CastValue(list[object], BuildValue["vertices_m"]))
    assert (
        Geometry["point_count"] == Geometry["line_count"] == PointCount
        and Geometry["endpoint_handles"] == 2 * PointCount
    )
    DepthValue = CastValue(dict[str, object], Prepared["driving_depth"])
    assert (
        DepthValue["native_name"] == "D1"
        and DepthValue["length_m"] == BuildValue["depth_m"]
    )
    assert (
        DepthValue["persistent_id"] == Dimensions[0]
        and DepthValue["actual_handle"] is True
    )
    Failures = CastValue(list[dict[str, object]], BuildValue["malformed"])
    assert len(Failures) == RejectionCount and all(
        RowValue["rejected"] for RowValue in Failures
    )
    for ReportValue in (BuildValue, Prepared):
        UsageValue = CastValue(dict[str, dict[str, object]], ReportValue["usage"])
        assert all(
            RowValue["completed"]
            and not RowValue["missing_schemas"]
            and not RowValue["provisional_schemas"]
            for RowValue in UsageValue.values()
        )
    assert Counterpart["explicit_active_list_initialization"] == [
        "f9d8",
        "fa48",
        "fa50",
    ]
    return CastValue(int, BuildValue["bytes"])
