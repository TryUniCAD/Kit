from hashlib import sha256 as CalcSha
from io import BytesIO
from json import loads as LoadJson
from math import isclose as IsClose
from os import environ as ProcessEnv
from pathlib import Path as FilePath
from subprocess import run as RunProcess
import sys
from tempfile import TemporaryDirectory as TempDir
from typing import cast as CastValue
from zlib import ZLIB_RUNTIME_VERSION as DeflateRuntime

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from convert.api import open_document as OpenDocument, write_document as WriteDocument
from interchange.Enums.EnumGeometry import GeometryKind
from tests.Convert.Commands.CliProcess import CliProcess
from tests.Convert.Solidworks.PlainWriting.MeasurePlainDoc import MeasurePlainDoc

# anchor paths relative to the checked out repository root
KRepoRoot = FilePath(__file__).resolve().parents[4]

# committed rectangular blind boss control part for milestone one
KSourcePart = (
    KRepoRoot
    / "re/automation/PairedCaptures/P03/solidworks-db1390476325/P03-solidworks-baseline-a.SLDPRT"
)

# independent solidworks measurement inventory for the control part
KSourceMeasure = (
    KRepoRoot
    / "re/automation/PairedCaptures/P03/solidworks-db1390476325/measurements.json"
)

# offline preparation script for milestone one candidates
KPrepareScript = KRepoRoot / "re/tooling/sw2026/PrepareBlindBossMilestone.py"

# donor replay detector guarding generated source modules
KCheckReplaysScript = KRepoRoot / "tools/Donors/CheckReplays.py"

# committed windows cli and sdk parity receipt
KParityReceipt = (
    KRepoRoot / "re/solidworks/measurements/2026/PlainPartWindowsCliParity01.json"
)


# verify the cli decode json payload matches the independent solidworks inventory
def VerifyDecodeCli(
    Baseline: dict[str, object],
    ExpectedParams: dict[str, float],
) -> None:
    with TempDir() as FolderName:
        Folder = FilePath(FolderName)
        DecodedPath = Folder / "Decoded.json"
        Outcome = CliProcess(
            Folder,
            "decode",
            str(KSourcePart),
            "-o",
            str(DecodedPath),
            "--overwrite",
        )
        assert Outcome.returncode == 0 and not Outcome.stderr, Outcome.stderr
        Payload = CastValue(dict[str, object], LoadJson(DecodedPath.read_text("utf-8")))
        assert Payload["kind"] == "kit.decode" and Payload["partial"] is False
        DocJson = CastValue(dict[str, object], Payload["document"])
        JsonBodies = CastValue(
            list[dict[str, object]],
            CastValue(dict[str, object], DocJson["bodies"])["$tuple"],
        )
        assert len(JsonBodies) == Baseline["body_count"] == 1
        JsonTopo = CastValue(dict[str, object], JsonBodies[0]["topology"])
        assert IsClose(
            CastValue(float, JsonTopo["volume"]),
            CastValue(float, Baseline["volume_mm3"]),
            rel_tol=1e-9,
        )
        JsonParams = {
            CastValue(str, ParamItem["name"]): CastValue(
                float, CastValue(dict[str, object], ParamItem["value"])["value"]
            )
            for ParamItem in CastValue(
                list[dict[str, object]],
                CastValue(dict[str, object], DocJson["parameters"])["$tuple"],
            )
        }
        assert JsonParams == ExpectedParams


# decoding the committed rectangular blind boss must match its independent inventory
def TestDecode() -> None:
    Measurements = CastValue(
        dict[str, object], LoadJson(KSourceMeasure.read_text("utf-8"))
    )
    Observations = CastValue(dict[str, object], Measurements["observations"])
    Baseline = CastValue(dict[str, object], Observations["baseline"])
    FeatureTree = CastValue(list[dict[str, object]], Baseline["feature_tree"])
    ExpectedParams = {
        CastValue(str, DimItem["name"]): CastValue(float, DimItem["system_value"])
        * 1000.0
        for NodeItem in FeatureTree
        for DimItem in CastValue(
            list[dict[str, object]], NodeItem.get("dimensions", [])
        )
    }
    VerifyDecodeCli(Baseline, ExpectedParams)
    Document = OpenDocument(KSourcePart, strict=True)
    assert len(Document.bodies) == Baseline["body_count"] == 1
    BodyValue = Document.bodies[0]
    assert BodyValue.topology.volume is not None
    assert IsClose(
        BodyValue.topology.volume,
        CastValue(float, Baseline["volume_mm3"]),
        rel_tol=1e-9,
    )
    Centroid = CastValue(
        tuple[float, float, float], BodyValue.attributes["solidworks.body_centroid_mm"]
    )
    ExpectedCentroid = CastValue(list[float], Baseline["center_of_mass_mm"])
    assert all(
        IsClose(Actual, Expected, rel_tol=1e-9)
        for Actual, Expected in zip(Centroid, ExpectedCentroid, strict=True)
    )
    ParamValues = {Param.name: Param.value.value for Param in Document.parameters}
    assert set(ParamValues) == set(ExpectedParams)
    assert all(
        IsClose(
            CastValue(float, ParamValues[NameKey]),
            ExpectedParams[NameKey],
            rel_tol=1e-9,
        )
        for NameKey in ExpectedParams
    )
    assert len(Document.sketches) == 1
    assert len(Document.sketches[0].closed_profile_entity_ids[0]) == 4


# verify one prepared candidate part round trips with expected geometry sketch and plane
def VerifyBossEntry(
    Entry: dict[str, object],
    ExpectedDepth: float,
    ExpectedVol: float,
    ExpectedCenter: list[float],
) -> None:
    PartPath = FilePath(CastValue(str, Entry["part_file"]))
    RawBytes = PartPath.read_bytes()
    assert CalcSha(RawBytes).hexdigest() == Entry["candidate_sha256"]
    Readback = OpenDocument(RawBytes, strict=True)
    assert len(Readback.bodies) == 1
    assert Readback.bodies[0].topology.volume is not None
    assert IsClose(Readback.bodies[0].topology.volume, ExpectedVol, rel_tol=1e-9)
    BodyCenter = CastValue(
        tuple[float, float, float],
        Readback.bodies[0].attributes["solidworks.body_centroid_mm"],
    )
    assert all(
        IsClose(Actual, Expected, rel_tol=1e-9)
        for Actual, Expected in zip(BodyCenter, ExpectedCenter, strict=True)
    )
    assert len(Readback.sketches) == 1
    SketchValue = Readback.sketches[0]
    assert len(SketchValue.entities) == 4
    assert all(
        EntityItem.kind == GeometryKind.KLine for EntityItem in SketchValue.entities
    )
    assert len(SketchValue.closed_profile_entity_ids) == 1
    assert len(SketchValue.closed_profile_entity_ids[0]) == 4
    PlaneNames = [
        PlaneItem.name
        for PlaneItem in Readback.support_planes
        if PlaneItem.id == SketchValue.support_plane_id
    ]
    assert PlaneNames == ["Front Plane"]
    (Driver,) = Readback.parameters
    assert (Driver.name, Driver.value.value, Driver.value.unit) == (
        "D1",
        ExpectedDepth,
        "mm",
    )
    ColdValue = PrepareNative(
        Readback,
        BytesIO(),
        CastValue(int, Entry["written_at"]),
        WriteOptions(values={"final_destination": Entry["native_locator"]}),
    )
    assert ColdValue.BytesValue == RawBytes


# offline preparation must produce deterministic baseline and edited candidates that round trip cleanly
def TestPrepBoss() -> None:
    with TempDir() as FolderName:
        Scratch = FilePath(FolderName) / "Milestone"
        PrepRun = RunProcess(
            [sys.executable, str(KPrepareScript), "--scratch", str(Scratch)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert PrepRun.returncode == 0, PrepRun.stdout + PrepRun.stderr
        ManifestPath = Scratch / "MilestoneManifest.json"
        Manifest = CastValue(
            dict[str, object], LoadJson(ManifestPath.read_text(encoding="utf-8"))
        )
        Candidates = CastValue(dict[str, dict[str, object]], Manifest["candidates"])
        Baseline = Candidates["baseline_10mm"]
        Edited = Candidates["edited_15mm"]
        ExpectedDelta = CastValue(dict[str, object], Manifest["expected_delta"])
        assert Baseline["runtime_input_reads"] == 0
        assert Edited["runtime_input_reads"] == 0
        for Entry, ExpectedDepth, ExpectedVol, ExpectedCenter in (
            (Baseline, 10.0, 8000.0, ExpectedDelta["expected_centroid_mm_before"]),
            (Edited, 15.0, 12000.0, ExpectedDelta["expected_centroid_mm_after"]),
        ):
            VerifyBossEntry(
                Entry,
                ExpectedDepth,
                ExpectedVol,
                CastValue(list[float], ExpectedCenter),
            )


# sdk direct adapter and cli publication must match the committed measurement parity receipts
def TestSdkParity() -> None:
    RuntimeName = "zlib-ng" if "zlib-ng" in DeflateRuntime else "classic"
    ParityData = CastValue(
        dict[str, object], LoadJson(KParityReceipt.read_text(encoding="utf-8"))
    )
    ParityRows = CastValue(list[dict[str, object]], ParityData["rows"])
    for RowValue in ParityRows:
        if RowValue["runtime"] != RuntimeName:
            continue
        RoleName = CastValue(str, RowValue["role"])
        Document, Envelope, Digest = MeasurePlainDoc(RoleName)
        assert Digest == RowValue["sha256"]
        NameValue = CastValue(str, Document.metadata["name"])
        Options = {
            "final_destination": rf"C:\KitSdkCandidates\{NameValue}.SLDPRT",
            KPartMeasureOpt: Envelope,
            "require_native_transfers": True,
        }
        SdkSink = BytesIO()
        DirectSink = BytesIO()
        SdkOut = WriteDocument(
            Document,
            SdkSink,
            destination_format=KPartFormatId,
            allow_carrier=False,
            values=Options,
        )
        DirectOut = SldprtWriter().write(
            Document, DirectSink, WriteOptions(values=Options)
        )
        assert SdkOut.vendor_loadable and SdkOut.application_usable
        assert DirectOut.vendor_loadable and DirectOut.application_usable
        assert SdkSink.getvalue() == DirectSink.getvalue()
        assert len(SdkSink.getvalue()) == RowValue["bytes"]
        assert CalcSha(SdkSink.getvalue()).hexdigest() == Digest


# donor replay checker must continue to report zero recorded payloads under src
def TestNoReplays() -> None:
    ReplayRun = RunProcess(
        [sys.executable, str(KCheckReplaysScript), str(KRepoRoot / "src")],
        cwd=str(KRepoRoot),
        env={**ProcessEnv, "PYTHONPATH": str(KRepoRoot)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert ReplayRun.returncode == 0, ReplayRun.stdout + ReplayRun.stderr
    assert "no recorded payloads" in ReplayRun.stdout
