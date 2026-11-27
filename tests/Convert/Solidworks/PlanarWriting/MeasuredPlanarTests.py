from contextlib import chdir as WithDirectory
from copy import deepcopy as CopyValue
from dataclasses import replace as ReplaceValue
from hashlib import sha256 as CalcSha
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath

from pytest import raises as RaisesError

from convert import open_document as OpenDocument, write_document as WriteDocument
from convert.adapters.base.ReadOptions import ReadOptions
from convert.api.ApiContext import KConvertEngine
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
    Settings: dict[str, object] = {
        **OptionsValue,
        "solidworks_native_measurement": Proof["measurement"],
    }
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
    ReplayPair(
        VerifyMateRead(TargetValue),
        TmpPath / "Reopened" / TargetValue.name,
        Expected,
        Settings,
    )
    ReplayRelPair(TargetValue, Expected, Settings)
    VerifyDeferred(TargetValue)


# the recorded root locator survives a relative source and a change in working directory
def ReplayRelPair(
    TargetValue: FilePath, Expected: dict[str, str], Settings: dict[str, object]
) -> None:
    with (
        WithDirectory(TargetValue.parent),
        FilePath(TargetValue.name).open("rb") as Source,
    ):
        Relative = OpenDocument(Source, source_format="solidworks.sldasm", strict=True)
    assert Relative.source.path == TargetValue.name
    ReplayPair(
        CadDocument.from_json(Relative.to_json(indent=None)),
        TargetValue.parent / "Relative" / TargetValue.name,
        Expected,
        Settings,
    )


# deferred component reading retains the physical mate payload for later resolution
def VerifyDeferred(TargetValue: FilePath) -> None:
    Deferred = KConvertEngine.read(
        TargetValue,
        format_id="solidworks.sldasm",
        options=ReadOptions(
            strict=True,
            values={"resolve_components": False, "discover_companions": False},
        ),
    )
    assert Deferred.assembly is not None and not Deferred.assembly.documents
    assert len(Deferred.assembly.instances) == 2
    Reopened = CadDocument.from_json(Deferred.to_json(indent=None))
    GraphValue = Reopened.assembly
    assert GraphValue is not None
    assert tuple(str(Value.kind) for Value in GraphValue.mates) == (
        "coincident",
        "distance",
    )
    ResolvedGraph = OpenDocument(TargetValue, strict=True).assembly
    assert ResolvedGraph is not None
    assert len(GraphValue.mate_entities) == 4
    assert tuple(
        (Value.id, Value.instance_path, Value.source_entity_id)
        for Value in GraphValue.mate_entities
    ) == tuple(
        (Value.id, Value.instance_path, Value.source_entity_id)
        for Value in ResolvedGraph.mate_entities
    )
    assert {Value.id for Value in GraphValue.mate_entities} == {
        Identity for RuleValue in GraphValue.mates for Identity in RuleValue.entity_ids
    }
    (GroupValue,) = GraphValue.mate_groups
    assert GroupValue.mate_ids == tuple(Value.id for Value in GraphValue.mates)
    assert (GroupValue,) == ResolvedGraph.mate_groups
    (DriverId,) = GraphValue.mates[1].parameter_ids
    assert Reopened.parameter(DriverId).value == GraphValue.mates[1].value
    assert Reopened.parameter(DriverId).value.value == 42.0
    assert Deferred.metadata["solidworks.typed_mates_semantics"] == {
        "status": "deferred",
        "full_selected_mate_graph": False,
        "public_writer_qualified": False,
    }
    assert any(
        Value.format_id == "solidworks.mates" for Value in Deferred.brep_payloads
    )


# measured output after a complete sdk reopen must retain both files and their exact evidence
def ReplayPair(
    Reopened: CadDocument,
    TargetValue: FilePath,
    Expected: dict[str, str],
    Settings: dict[str, object],
) -> None:
    Result = WriteDocument(Reopened, TargetValue, allow_carrier=False, values=Settings)
    assert Result.application_usable and Result.vendor_loadable and not Result.dropped
    VerifyPairFiles(TargetValue.parent, Expected)


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
