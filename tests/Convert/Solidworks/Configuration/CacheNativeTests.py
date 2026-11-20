from typing import cast as CastValue

from tests.Convert.Solidworks.Configuration.RunCacheCase import RunCacheCase

# the tracked parts exercise the same empty caches after two distinct native map histories
KCacheCounters = (("ladder", 108, 110), ("concave", 94, 94))

# the empty mass record ends immediately after its slot count
KEmptyMass: dict[str, object] = {"f1628": [], "f1638": 0}

# the empty bounds record has no tagged owners to add to the archive map
KEmptyBounds: dict[str, object] = {"f1640": []}


# the two native parts retain their exact empty records and incoming map counters
def TestCacheOwners() -> None:
    for CaseName, MassCounter, BoundsCounter in KCacheCounters:
        ReportValue = RunCacheCase(CaseName)
        Records = CastValue(dict[str, dict[str, object]], ReportValue["records"])
        MassValue = Records["mass"]
        BoundsValue = Records["bounds"]
        assert MassValue["fields"] == KEmptyMass
        assert BoundsValue["fields"] == KEmptyBounds
        assert MassValue["counter"] == MassCounter
        assert BoundsValue["counter"] == BoundsCounter
        for RecordValue in (MassValue, BoundsValue):
            assert RecordValue["bytes"] == 4
            assert RecordValue["anchor_slots"] == [1, 2, 3]
            assert RecordValue["layouts"] == []
