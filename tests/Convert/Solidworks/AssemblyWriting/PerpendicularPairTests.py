from tests.Convert.Solidworks.AssemblyWriting.RunPublicWrite import RunPublicWrite


# valid perpendicular geometry still constructs both files while the planar receipt cannot authorize either profile
def TestPerpPair() -> None:
    Valid = RunPublicWrite("legacy-perp")
    Invalid = RunPublicWrite("legacy-perp-invalid")
    assert Valid["generated_model_members"] == 2
    assert Valid["generated_stream_counts"] == [12, 10]
    assert Invalid["generated_model_members"] == 0
    for Report in (Valid, Invalid):
        assert Report["writer_native_flags"] is False
        assert Report["before"] == Report["after"] == {}
        assert Report["error"] is not None
