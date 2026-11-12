from dataclasses import fields as DataFields, is_dataclass as IsDataClass
from io import BytesIO
from pathlib import Path as FilePath
from sys import version_info as PythonVersion
from typing import cast as CastValue
from zipfile import ZipFile

from pytest import mark as TestMark

from convert.formats.Fusion.DocumentCodec.EmitParsed import EmitParsed
from convert.formats.Fusion.DocumentCodec.ReadDocument import ReadDocument
from convert.formats.Fusion.EntityCodec.Model.CrossRef import CrossRef
from convert.formats.Fusion.SegmentCodec.Manifest.LinkLayout import (
    KLinkedAsset,
    KLinkedUrl,
)

KFixtures = (
    FilePath(__file__).resolve().parents[5]
    / "re"
    / "Fusion"
    / "LocalOracle"
    / "LinksConfigs"
    / "Fixtures"
)

KRequiresCodec = TestMark.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)

KReencoded = (".protein", ".smb", ".smbh")

KLinkCounts = (
    ("P_A1_saved", 0, ()),
    ("P_B1_saved", 0, ()),
    ("R0_empty", 0, ()),
    ("R1_part_a", 1, ("KitLinkPartA",)),
    ("R2_grounded", 1, ("KitLinkPartA",)),
    ("R3_nested", 2, ("KitLinkPartA", "KitLinkSub")),
    ("R4_joint", 2, ("KitLinkPartA", "KitLinkSub")),
    ("R5_saved", 2, ("KitLinkPartA", "KitLinkSub")),
    ("R6_out_of_date", 2, ("KitLinkPartA", "KitLinkSub")),
    ("R7_updated", 2, ("KitLinkPartA", "KitLinkSub")),
    ("R8_updated_saved", 2, ("KitLinkPartA", "KitLinkSub")),
    ("R9_archive", 2, ("KitLinkPartA", "KitLinkSub")),
    ("S0_inserted", 1, ("KitLinkPartB",)),
    ("S1_saved", 1, ("KitLinkPartB",)),
)

KControls = tuple(Entry[0] for Entry in KLinkCounts)


def ReadMembers(DataValue: bytes) -> dict[str, bytes]:
    with ZipFile(BytesIO(DataValue)) as Archive:
        return {Entry: Archive.read(Entry) for Entry in Archive.namelist()}


def CollectCross(Value: object, Found: list[CrossRef]) -> list[CrossRef]:
    if isinstance(Value, CrossRef):
        Found.append(Value)
    elif isinstance(Value, tuple):
        for Entry in CastValue(tuple[object, ...], Value):
            _ = CollectCross(Entry, Found)
    elif IsDataClass(Value) and not isinstance(Value, type):
        for FieldInfo in DataFields(Value):
            _ = CollectCross(getattr(Value, FieldInfo.name), Found)
    return Found


def LoadFixture(StemName: str) -> bytes:
    return (KFixtures / f"{StemName}.f3d").read_bytes()


@KRequiresCodec
@TestMark.parametrize("StemName", KControls)
def TestLinkReplay(StemName: str) -> None:
    Source = LoadFixture(StemName)
    Model = ReadDocument(Source)
    Output = EmitParsed(Model)
    assert ReadDocument(Output) == Model
    Before, After = ReadMembers(Source), ReadMembers(Output)
    assert set(Before) == set(After)
    Changed = {
        Entry
        for Entry in Before
        if Before[Entry] != After[Entry] and not Entry.endswith(KReencoded)
    }
    assert not Changed


@KRequiresCodec
@TestMark.parametrize("StemName,LinkCount,Targets", KLinkCounts)
def TestLinkTables(StemName: str, LinkCount: int, Targets: tuple[str, ...]) -> None:
    Model = ReadDocument(LoadFixture(StemName))
    RootLinks = Model.Document.Links
    assert len(RootLinks) == len(Model.Asset.Links) == LinkCount
    assert (
        tuple(sorted(dict(Entry.Properties)["toDocDisplayName"] for Entry in RootLinks))
        == Targets
    )
    Assets = {Entry.LinkId: Entry.AssetId for Entry in Model.Asset.Links}
    for Entry in RootLinks:
        Fields = dict(Entry.Properties)
        assert Fields[KLinkedAsset] == Assets[Entry.LinkId]
        assert Fields[KLinkedUrl].startswith("urn:adsk.wipprod:fs.file:vf.")
    for Segment in Model.Segments:
        Contexts = Segment.Metadata.Contexts
        assert len(Contexts) == LinkCount
        assert {Entry.LinkId for Entry in Contexts} == set(Assets)
        Tokens = {Entry.Token for Entry in Contexts}
        Crossing = CollectCross(Segment.Records, [])
        assert bool(Crossing) == bool(LinkCount)
        assert all(Entry.Token in Tokens for Entry in Crossing)


@KRequiresCodec
def TestLinkUpdate() -> None:
    Stale = ReadDocument(LoadFixture("R6_out_of_date"))
    Fresh = ReadDocument(LoadFixture("R7_updated"))
    StaleIds = {Entry.LinkId for Entry in Stale.Document.Links}
    FreshIds = {Entry.LinkId for Entry in Fresh.Document.Links}
    assert len(StaleIds - FreshIds) == len(FreshIds - StaleIds) == 1
    Urls = {
        dict(Entry.Properties)["toDocDisplayName"]: dict(Entry.Properties)[KLinkedUrl]
        for Entry in Fresh.Document.Links
    }
    assert Urls["KitLinkPartA"].endswith("?version=2")
    assert Urls["KitLinkSub"].endswith("?version=1")


@KRequiresCodec
def TestSharedTokens() -> None:
    Model = ReadDocument(LoadFixture("R3_nested"))
    Tokens = {
        Segment.Metadata.Header.Segment.name: {
            Entry.LinkId: (Entry.Token, Entry.SegmentId)
            for Entry in Segment.Metadata.Contexts
        }
        for Segment in Model.Segments
    }
    assert Tokens["KDesign"] == Tokens["KBrowser"]
    assert all(SegmentId == 0 for _, SegmentId in Tokens["KDesign"].values())
    assert all(SegmentId == 1 for _, SegmentId in Tokens["KAct"].values())
    assert all(
        Tokens["KAct"][LinkId][0] != Token
        for LinkId, (Token, _) in Tokens["KDesign"].items()
    )
