from copy import deepcopy as CopyValue
from dataclasses import replace as ReplaceValue
from hashlib import sha256 as CalcSha
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath

from pytest import raises as RaisesError

from convert import open_document as OpenDocument, write_document as WriteDocument
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumDocument import Capability

# queue tests use the same neutral request and native measurement as the disclosed bundle
KPlanarFixtures = (
    FilePath(__file__).resolve().parents[4]
    / "re/solidworks/measurements/2026/MeasuredPlanarPair"
)


# explicit native evidence must bind every file before the registry publishes a new bundle
def TestPlanarWrite(TmpPath: FilePath) -> None:
    Request = LoadJson((KPlanarFixtures / "NeutralRequest.json").read_bytes())
    Proof = LoadJson((KPlanarFixtures / "MeasuredOutput.json").read_bytes())
    Document = CadDocument.from_json(DumpJson(Request["document"]))
    TargetValue = TmpPath / "PublicPlanarPair2.SLDASM"
    OptionsValue = {
        "native_destination": Request["native_parent"],
        "require_native_transfers": True,
    }
    with RaisesError(ValueError, match="requires an offline native measurement"):
        _ = WriteDocument(Document, TargetValue, values=OptionsValue)
    WrongValue = CopyValue(Proof["measurement"])
    WrongValue["receipt"]["members"][0]["sha256"] = "0" * 64
    with RaisesError(
        ValueError, match="does not match the exact member PublicDatumPrism"
    ):
        _ = WriteDocument(
            Document,
            TargetValue,
            values={**OptionsValue, "solidworks_native_measurement": WrongValue},
        )
    assert not tuple(TmpPath.iterdir())
    GraphValue = Document.assembly
    assert GraphValue is not None
    Document = ReplaceValue(
        Document,
        assembly=ReplaceValue(GraphValue, mates=tuple(reversed(GraphValue.mates))),
        capabilities=Document.capabilities | {Capability.KAssemblyMates},
    )
    Settings = {**OptionsValue, "solidworks_native_measurement": Proof["measurement"]}
    ResultValue = WriteDocument(
        Document,
        TargetValue,
        allow_carrier=False,
        values=Settings,
    )
    assert ResultValue.application_usable and ResultValue.vendor_loadable
    assert not ResultValue.dropped
    Expected = {
        NameValue: RowValue["sha256"] for NameValue, RowValue in Proof["files"].items()
    }
    VerifyPairFiles(TmpPath, Expected)
    ReplayPair(VerifyMateRead(TargetValue), TargetValue, Expected, Settings)


# measured output after a complete sdk reopen must retain both files and their exact evidence
def ReplayPair(
    Reopened: CadDocument,
    TargetValue: FilePath,
    Expected: dict[str, str],
    Settings: dict[str, object],
) -> None:
    Replay = TargetValue.parent / "Reopened"
    Result = WriteDocument(
        Reopened, Replay / TargetValue.name, allow_carrier=False, values=Settings
    )
    assert Result.application_usable and Result.vendor_loadable and not Result.dropped
    VerifyPairFiles(Replay, Expected)


# both generated members must retain their complete measured file identities
def VerifyPairFiles(Folder: FilePath, Expected: dict[str, str]) -> None:
    assert {
        Value.name: CalcSha(Value.read_bytes()).hexdigest()
        for Value in Folder.iterdir()
    } == Expected


# confirmed fixed state and endpoint ownership require the full typed reader
def VerifyMateRead(TargetValue: FilePath) -> CadDocument:
    Reopened = OpenDocument(TargetValue, strict=True)
    GraphValue = Reopened.assembly
    assert GraphValue is not None
    assert tuple(Value.fixed for Value in GraphValue.instances) == (True, False)
    assert len(GraphValue.mate_groups) == 1 and len(GraphValue.mate_entities) == 4
    assert tuple(str(Value.kind) for Value in GraphValue.mates) == (
        "coincident",
        "distance",
    )
    DistanceValue = GraphValue.mates[1].value
    assert DistanceValue is not None and DistanceValue.value == 42.0
    (DriverId,) = GraphValue.mates[1].parameter_ids
    DriverValue = Reopened.parameter(DriverId)
    assert DriverValue.name == "D1" and DriverValue.value == DistanceValue
    assert DriverValue.owner_id == GraphValue.mates[1].id
    assert (
        DriverValue.provenance is not None and DriverValue.provenance.native_id == "20"
    )
    assert len(GraphValue.documents[0].document.parameters) == 3
    return Reopened
