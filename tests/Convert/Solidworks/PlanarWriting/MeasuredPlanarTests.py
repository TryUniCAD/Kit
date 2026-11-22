from hashlib import sha256 as CalcSha
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath

from pytest import raises as RaisesError

from convert import open_document as OpenDocument, write_document as WriteDocument
from interchange.document.Models.DocumentModel import CadDocument

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
    assert not tuple(TmpPath.iterdir())
    ResultValue = WriteDocument(
        Document,
        TargetValue,
        allow_carrier=False,
        values={
            **OptionsValue,
            "solidworks_native_measurement": Proof["measurement"],
        },
    )
    assert ResultValue.application_usable and ResultValue.vendor_loadable
    assert not ResultValue.dropped
    assert {
        Value.name: CalcSha(Value.read_bytes()).hexdigest()
        for Value in TmpPath.iterdir()
    } == {
        NameValue: RowValue["sha256"] for NameValue, RowValue in Proof["files"].items()
    }
    VerifyMateRead(TargetValue)


# confirmed fixed state and endpoint ownership require the full typed reader
def VerifyMateRead(TargetValue: FilePath) -> None:
    Reopened = OpenDocument(TargetValue, strict=True)
    GraphValue = Reopened.assembly
    assert GraphValue is not None
    assert tuple(Value.fixed for Value in GraphValue.instances) == (True, False)
    assert len(GraphValue.mate_groups) == 1 and len(GraphValue.mate_entities) == 4
    assert tuple(Value.kind.value for Value in GraphValue.mates) == (
        "coincident",
        "distance",
    )
    DistanceValue = GraphValue.mates[1].value
    assert DistanceValue is not None and DistanceValue.value == 42.0
    assert len(GraphValue.documents[0].document.parameters) == 3
