from tests.Convert.Solidworks.Configuration.RunHeadLink import RunHeadLink


# ordered header references and logical version checks use the same physical archive boundary
def TestHeadAlias() -> None:
    ReportValue = RunHeadLink("authored")
    assert ReportValue["aliases"] == [
        ["AliasSelf", "RootConfig", 301],
        ["ZuluRef", "ZuluConfig", 923],
        ["AlphaRef", "AlphaConfig", 117],
    ]
    assert ReportValue["source_indices"] == [12, 6, 10]
    assert ReportValue["config_slots"] == [3, 4, 5]
    assert ReportValue["base"] == ReportValue["counter"] == 6
    assert ReportValue["lightweight_span"] == [18, 26]
    assert ReportValue["physical_format"] == 4
    assert ReportValue["logical_versions"] == [19000, 18900]
    assert ReportValue["refusals"] == ["other_logical_version"]
