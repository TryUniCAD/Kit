"""Checkable ledger of everything this repository claims about the Creo adapter.

Every line printed here corresponds to a statement in
`Documentation/Changes/Creo/CreoGenerativeAuthor.md`. Run it to confirm the claims still hold:

    PYTHONPATH=src python3 re/creo/tools/Verify.py

It needs no Creo: these are the byte-level and reader-level facts. Anything that requires a Creo launch is marked
`external` and is not checked here, because a launch cannot be replayed in CI.

Vendor files are research oracles and are never shipped.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "re/creo/tools")

import Subset
from convert.adapters.creo import Author
from convert.adapters.creo import VisibGeom
from convert.adapters.creo.Adapter import CreoAdapter
from convert.adapters.creo.Header import ReadHeader
from convert.adapters.creo.Stream import StreamParser

KEmpty = Path("re/creo/oracle/empty/solid_start_part_mmks.prt")
KLadder = Path("re/creo/oracle/ladder/ladder1.prt.2")
KResults: list[tuple[str, bool, str]] = []


def Check(Name: str, Passed: bool, Detail: str) -> None:
    KResults.append((Name, Passed, Detail))


def CheckRebuilds() -> None:
    for PathValue in (KEmpty, KLadder):
        DataValue = PathValue.read_bytes()
        Header = ReadHeader(DataValue)
        Result = Subset.Build(DataValue, Header.base, set(), {})
        Check(
            f"no-op rebuild {PathValue.name}",
            Result == DataValue,
            f"{len(DataValue)} bytes",
        )


def CheckReader() -> None:
    Document = CreoAdapter().read(KLadder)
    Body = Document.bodies[0]
    Check(
        "reader ladder counts",
        (
            len(Document.feature_timeline),
            len(Document.parameters),
            Body.topology.face_count,
            Body.topology.edge_count,
            Body.topology.solid_count,
        )
        == (7, 8, 6, 12, 1),
        f"{len(Document.feature_timeline)} features, {len(Document.parameters)} params, "
        f"{Body.topology.face_count} faces, {Body.topology.edge_count} edges, "
        f"{Body.topology.solid_count} solid",
    )
    Check(
        "reader ladder volume",
        abs(Body.topology.volume - 18482541.490319017) < 1e-6,
        f"{Body.topology.volume}",
    )
    Empty = CreoAdapter().read(KEmpty)
    Check(
        "reader empty control",
        (len(Empty.feature_timeline), len(Empty.bodies)) == (4, 0),
        f"{len(Empty.feature_timeline)} features, {len(Empty.bodies)} bodies",
    )


def CheckVolume() -> None:
    DataValue = KLadder.read_bytes()
    Header = ReadHeader(DataValue)
    for TableValue in Subset.ReadTables(DataValue, Header.base):
        for Entry in TableValue.rows:
            if Entry.name != "VisibGeom":
                continue
            Offset = Header.base + Entry.offset
            Body = DataValue[Offset : Offset + Entry.length]
            Payload = Body[Body.find(b"\n") + 1 :]
    Surfaces, _Curves = VisibGeom.ReadGeometry(Payload)
    Projections: dict[int, list[float]] = {0: [], 1: [], 2: []}
    for Surface in Surfaces:
        Plane = VisibGeom.PlaneValue(Surface)
        if Plane is None:
            continue
        Normal, OffsetValue = Plane
        Axis = max(range(3), key=lambda Index: abs(Normal[Index]))
        Projections[Axis].append(OffsetValue if Normal[Axis] > 0 else -OffsetValue)
    Spans = [max(Values) - min(Values) for Values in Projections.values()]
    Independent = Spans[0] * Spans[1] * Spans[2]
    Reported = CreoAdapter().read(KLadder).bodies[0].topology.volume
    Check(
        "volume cross-checked by plane spans",
        abs(Independent - Reported) < 1e-6,
        f"{Independent:.6f} from spans, {Reported:.6f} from the reader",
    )


def CheckEmitters() -> None:
    AllFeatur = Author.DefaultAllFeatur()
    Payload = Author.StripSectionHeader("AllFeatur", AllFeatur)
    Check(
        "generated AllFeatur",
        len(Payload) == 1876 and Payload.count(b"\xE0\x00feat_defs") == 0,
        f"{len(Payload)} bytes, 4 records",
    )
    FeatDefs = Author.DefaultFeatDefs((100.0, 42.5))
    Check(
        "generated FeatDefs",
        b"place_rec_ptr" in FeatDefs and FeatDefs.count(b"dimtab_ptr") == 1,
        f"{len(FeatDefs)} bytes, one definition with placement",
    )
    Protrusion = Author.SolidFeatureDefinition(74, (100.0,))
    Check(
        "generated class 917 element",
        len(Protrusion) == 346 and b"place_rec_ptr" in Protrusion,
        f"{len(Protrusion)} bytes",
    )


def CheckReplay() -> None:
    DataValue = KEmpty.read_bytes()
    Header = ReadHeader(DataValue)
    for TableValue in Subset.ReadTables(DataValue, Header.base):
        for Entry in TableValue.rows:
            if Entry.name != "AllFeatur":
                continue
            Offset = Header.base + Entry.offset
            Body = DataValue[Offset : Offset + Entry.length]
            Payload = Body[Body.find(b"\n") + 1 :]
    # a positional replay carries values only, so it must contain no field headers and stay shorter
    Definition = Author.DatumFeatureRecord(
        5,
        923,
        "TOP",
        6,
        -5778,
        (-1,) * 252,
        200000,
        200001,
        1000000000,
        12345,
        99,
        2,
        1,
        3,
    )
    Replay = Author.ReplayOf(Definition)
    Check(
        "ReplayOf is a headerless projection",
        b"\xE0\x00" not in Replay
        and len(Replay) < len(Definition)
        and Author.ReplayOf(Definition) == Replay,
        f"{len(Replay)} bytes against a {len(Definition)}-byte definition",
    )


def CheckGeneratedPart() -> None:
    Bodies = Author.EmptyPartSections()
    Bodies["VisibGeom"] = Author.EmptyVisibGeom()
    Check(
        "generated row count",
        len(Bodies) == 47,
        f"{len(Bodies)} generated rows",
    )
    DataValue = KEmpty.read_bytes()
    Header = ReadHeader(DataValue)
    for TableValue in Subset.ReadTables(DataValue, Header.base):
        for Entry in TableValue.rows:
            if Entry.name != "FeatDefsIndex":
                continue
            Offset = Header.base + Entry.offset
            Body = DataValue[Offset : Offset + Entry.length]
            Reference = Body[Body.find(b"\n") + 1 :]
    Ours = Author.StripSectionHeader("FeatDefsIndex", Bodies["FeatDefsIndex"])
    Check("definition index matches the control", Ours == Reference, Ours.hex(" "))


def CheckWriterFlags() -> None:
    Source = Path("src/convert/adapters/creo/Writer.py").read_text()
    Check(
        "writer reports replay only",
        '"mode": "exact_native_roundtrip"' in Source
        and '"vendor_loadable": False' in Source
        and '"application_usable": False' in Source,
        "mode, vendor_loadable and application_usable unchanged",
    )
    Check(
        "writer diagnostic names the real limit",
        "no authored Creo body has been measured" in Source,
        "diagnostic does not claim body authoring",
    )


def main() -> int:
    CheckRebuilds()
    CheckReader()
    CheckVolume()
    CheckEmitters()
    CheckReplay()
    CheckGeneratedPart()
    CheckWriterFlags()
    Width = max(len(Name) for Name, _, _ in KResults)
    for Name, Passed, Detail in KResults:
        print(f"{'PASS' if Passed else 'FAIL'}  {Name:<{Width}}  {Detail}")
    print()
    print("external, not checked here: Creo launches (see the change entry's reproduction section)")
    Failed = sum(1 for _, Passed, _ in KResults if not Passed)
    print(f"{len(KResults) - Failed} of {len(KResults)} checks pass")
    return 1 if Failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
