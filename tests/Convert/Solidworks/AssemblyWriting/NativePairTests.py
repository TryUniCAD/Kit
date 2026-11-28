from tests.Convert.Solidworks.AssemblyWriting.RunPublicWrite import RunPublicWrite


# deferred publication must match the entire measured bundle and report only location bound evidence
def TestNativePairs() -> None:
    for ModeValue in ("measured", "measured-explicit"):
        Report = RunPublicWrite(ModeValue)
        assert Report["matching_member_streams"] == 22
        assert Report["whole_bundle_matches_native_input"] is True
        assert Report["writer_native_flags"] is False
        assert Report["error"] is None


# existing portable mate constructors remain available independently of publication eligibility
def TestLegacyPairs() -> None:
    for ModeValue in ("legacy2", "legacy3"):
        Report = RunPublicWrite(ModeValue)
        assert Report["generated_model_members"] == 2
        assert Report["generated_stream_counts"] == [12, 10]
        assert Report["before"] == Report["after"] == {}
        assert Report["error"] is not None
