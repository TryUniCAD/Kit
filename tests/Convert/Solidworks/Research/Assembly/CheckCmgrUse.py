from typing import cast as CastValue


# shared dependency admission must describe actual sdk execution rather than an empty research usage set
def CheckCmgrUse(Report: dict[str, object]) -> None:
    (FileValue,) = CastValue(list[dict[str, object]], Report["files"])
    Streams = CastValue(dict[str, dict[str, object]], FileValue["streams"])
    UsageValue = CastValue(
        dict[str, dict[str, object]], Streams["Contents/CMgr"]["schema_usage"]
    )
    for Direction in ("load", "store"):
        Snapshot = UsageValue[Direction]
        (Shared,) = CastValue(list[dict[str, object]], Snapshot["shared_schema_usage"])
        assert Shared["codec"] == "sdk_ordinary_cmgr" and Shared["admitted"] is True
        assert Shared["source_streams"] == ["Contents/CMgr"]
        ActualUsage = CastValue(dict[str, object], Shared["usage"])
        assert ActualUsage["completed"] is True
        assert (
            ActualUsage["missing_schemas"] == ActualUsage["provisional_schemas"] == []
        )
        Names = CastValue(list[str], ActualUsage["used_schemas"])
        assert "moConfigurationMgr_c" in Names and len(Names) > 10
        assert set(Names) <= set(CastValue(list[str], Snapshot["used_schemas"]))
