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
from tests.Convert.Commands.CliProcess import CliProcess
from tests.Convert.Solidworks.PlainWriting.MeasurePlainDoc import MeasurePlainDoc
from tests.Convert.Solidworks.PlainWriting.VerifyCliMeas import VerifyCliMeas

# repository root and committed P03 rectangular blind-boss control paths
KRepoRoot = FilePath(__file__).resolve().parents[4]
KP03Source = (
    KRepoRoot
    / "re/automation/PairedCaptures/P03/solidworks-db1390476325/P03-solidworks-baseline-a.SLDPRT"
)
KP03Measurements = (
    KRepoRoot
    / "re/automation/PairedCaptures/P03/solidworks-db1390476325/measurements.json"
)
KPrepareScript = KRepoRoot / "re/tooling/sw2026/PrepareBlindBossMilestone.py"
KCheckReplaysScript = KRepoRoot / "tools/Donors/CheckReplays.py"
KParityReceipt = (
    KRepoRoot / "re/solidworks/measurements/2026/PlainPartWindowsCliParity01.json"
)


# decoding the committed rectangular blind boss must match its independent SOLIDWORKS inventory
def TestDecodeMatchesInventory() -> None:
    with TempDir() as FolderName:
        Folder = FilePath(FolderName)
        DecodedPath = Folder / "Decoded.json"
        Outcome = CliProcess(
            Folder,
            "decode",
            str(KP03Source),
            "-o",
            str(DecodedPath),
            "--overwrite",
        )
        assert Outcome.returncode == 0 and not Outcome.stderr, Outcome.stderr
        Payload = CastValue(dict[str, object], LoadJson(DecodedPath.read_text("utf-8")))
        assert Payload["kind"] == "kit.decode" and Payload["partial"] is False
    Document = OpenDocument(KP03Source, strict=True)
    Measurements = CastValue(
        dict[str, object], LoadJson(KP03Measurements.read_text("utf-8"))
    )
    Observations = CastValue(dict[str, object], Measurements["observations"])
    Baseline = CastValue(dict[str, object], Observations["baseline"])
    assert len(Document.bodies) == Baseline["body_count"] == 1
    Body = Document.bodies[0]
    assert Body.topology.volume is not None
    assert IsClose(
        Body.topology.volume,
        CastValue(float, Baseline["volume_mm3"]),
        rel_tol=1e-9,
    )
    Centroid = CastValue(
        tuple[float, float, float], Body.attributes["solidworks.body_centroid_mm"]
    )
    ExpectedCentroid = CastValue(list[float], Baseline["center_of_mass_mm"])
    assert all(
        IsClose(Actual, Expected, rel_tol=1e-9)
        for Actual, Expected in zip(Centroid, ExpectedCentroid, strict=True)
    )
    ParamValues = {Param.name: Param.value.value for Param in Document.parameters}
    assert ParamValues == {"width_mm": 40.0, "height_mm": 20.0, "depth_mm": 10.0}
    assert len(Document.sketches) == 1
    assert len(Document.sketches[0].closed_profile_entity_ids[0]) == 4


# offline milestone preparation must produce deterministic 10mm and 15mm candidates that round-trip cleanly
def TestPrepareMilestoneCandidates() -> None:
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
        assert Baseline["runtime_input_reads"] == 0
        assert Edited["runtime_input_reads"] == 0
        for Entry, ExpectedDepth, ExpectedVol in (
            (Baseline, 10.0, 8000.0),
            (Edited, 15.0, 12000.0),
        ):
            PartPath = FilePath(CastValue(str, Entry["part_file"]))
            RawBytes = PartPath.read_bytes()
            assert CalcSha(RawBytes).hexdigest() == Entry["candidate_sha256"]
            Readback = OpenDocument(RawBytes, strict=True)
            assert len(Readback.bodies) == 1
            assert Readback.bodies[0].topology.volume is not None
            assert IsClose(
                Readback.bodies[0].topology.volume, ExpectedVol, rel_tol=1e-9
            )
            (Driver,) = Readback.parameters
            assert (Driver.name, Driver.value.value, Driver.value.unit) == (
                "D1",
                ExpectedDepth,
                "mm",
            )
            Cold = PrepareNative(
                Readback,
                BytesIO(),
                CastValue(int, Entry["written_at"]),
                WriteOptions(
                    values={"final_destination": Entry["native_locator"]}
                ),
            )
            assert Cold.BytesValue == RawBytes


# sdk, direct adapter, and cli publication must match the committed measurement parity receipts
def TestSdkCliReceiptParity() -> None:
    RuntimeName = "zlib-ng" if "zlib-ng" in DeflateRuntime else "classic"
    ParityData = CastValue(
        dict[str, object], LoadJson(KParityReceipt.read_text(encoding="utf-8"))
    )
    ParityRows = CastValue(list[dict[str, object]], ParityData["rows"])
    for Row in ParityRows:
        if Row["runtime"] != RuntimeName:
            continue
        RoleName = CastValue(str, Row["role"])
        Document, Envelope, Digest = MeasurePlainDoc(RoleName)
        assert Digest == Row["sha256"]
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
        assert len(SdkSink.getvalue()) == Row["bytes"]
        assert CalcSha(SdkSink.getvalue()).hexdigest() == Digest
        with TempDir() as FolderName:
            VerifyCliMeas(FilePath(FolderName), RoleName)


# donor replay checker must continue to report zero recorded payloads under src
def TestCheckReplaysClean() -> None:
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
