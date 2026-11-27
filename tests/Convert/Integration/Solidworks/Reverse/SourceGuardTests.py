from hashlib import sha256 as HashBytes
from json import loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as TestMark, raises as RaisesError

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


# the bounded cold reader must retain the separate genuine source grammar refusal
@TestMark.parametrize(
    "CaseName",
    (
        "baseline-a",
        "baseline-b",
        "edit-width_mm-41",
        "edit-height_mm-23",
        "edit-depth_mm-12",
        "units-inch",
        "plane-yz",
        "direction-negative",
    ),
)
def CheckSourceGap(CaseName: str) -> None:
    RootPath = FilePath(__file__).resolve().parents[5]
    SourceRoot = RootPath / "re/automation/PairedCaptures/P03/solidworks-db1390476325"
    Source = SourceRoot / ("P03-solidworks-" + CaseName + ".SLDPRT")
    Receipt = LoadJson((SourceRoot / "receipt.json").read_text())
    Member = next(
        Value for Value in Receipt["native_files"] if Value["file"] == Source.name
    )
    DataValue = Source.read_bytes()
    assert HashBytes(DataValue).hexdigest() == Member["sha256"]
    Archive = SldprtArchive.from_bytes(DataValue, Source.name)
    with RaisesError(BodyUnsupported, match="moGhostBodyObject_c.FUN_4bf05390"):
        _ = ReadNativeLink(Archive, 0)
