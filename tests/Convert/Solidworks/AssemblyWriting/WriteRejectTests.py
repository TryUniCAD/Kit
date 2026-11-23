from tests.Convert.Solidworks.AssemblyWriting.RunPublicWrite import RunPublicWrite

# independently measured bundle rejections exercise both artifact identity and final publication policy
KRejectCases = (
    "child-collision",
    "case-collision",
    "directory-collision",
    "dangling-child",
    "root-collision",
    "overwrite",
    "overwrite-empty",
    "stream",
    "missing-mapping",
    "wrong-mapping",
    "relative-mapping",
    "wrong-format",
    "unqualified-option",
    "unsupported-mate",
    "unqualified-child",
    "named-child",
    "commit-failure",
    "no-receipt",
    "forged-receipt",
    "wrong-member",
    "wrong-native-locator",
    "unmeasured-location",
    "strict-deferred",
    "direct",
    "wrong-config",
)


# a refused graph or handled publication failure must preserve caller entries and remove its owned stage
def TestWriteReject() -> None:
    for ModeValue in KRejectCases:
        Report = RunPublicWrite(ModeValue)
        assert Report["before"] == Report["after"]
        assert Report["error"] is not None


# actual registry publication must retain an independently created competing companion
def TestPeerWrite() -> None:
    Report = RunPublicWrite("race-protection")
    assert Report["concurrent_companion_preserved"] is True
