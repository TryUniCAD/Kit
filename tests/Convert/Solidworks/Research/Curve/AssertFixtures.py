from __future__ import annotations

from typing import cast as CastValue
from tests.Convert.Solidworks.Research.Curve.CorpusPaths import KCurveCorpus, KCurveLock
from tests.Convert.Solidworks.Research.Curve.ReadObject import ReadObject
from tests.Convert.Solidworks.Research.Curve.AssertFixture import AssertFixture


# exact physical membership prevents missing controls and accidental held out payload publication
def AssertFixtures(Manifest: dict[str, object]) -> dict[str, dict[str, object]]:
    LockData = ReadObject(KCurveLock)
    LockedCases = CastValue(list[dict[str, object]], LockData["cases"])
    Expected = {
        CastValue(str, Entry["name"]): Entry
        for Entry in LockedCases
        if Entry["split"] in {"discovery", "control"}
    }
    Records = CastValue(list[dict[str, object]], Manifest["records"])
    Entries = {CastValue(str, Entry["name"]): Entry for Entry in Records}
    assert len(Records) == len(Entries) == len(Expected) == 26
    assert sum(Entry["split"] == "discovery" for Entry in Expected.values()) == 24
    assert {
        NameValue
        for NameValue, Entry in Expected.items()
        if Entry["split"] == "control"
    } == {"ControlCircle", "ControlRectangle"}
    assert set(Entries) == set(Expected)
    for NameValue, Entry in Entries.items():
        AssertFixture(Entry, Expected[NameValue])
    StoredFiles = {
        FileEntry.relative_to(KCurveCorpus).as_posix()
        for FileEntry in KCurveCorpus.rglob("*")
        if FileEntry.is_file()
    }
    assert StoredFiles == {f"{NameValue}.SLDPRT" for NameValue in Expected} | {
        "Manifest.json",
        "PrivacyLedger.json",
        "SourceEvidence.json",
    }
    return {CastValue(str, Entry["file"]): Entry for Entry in Records}
