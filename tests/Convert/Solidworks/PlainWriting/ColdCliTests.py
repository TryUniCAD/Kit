from hashlib import sha256 as CalcSha
from io import BytesIO
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as MarkTests

from convert.api.ApiConvert import ConvertFile
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.Writing.Measured.PartMeasureOpt import (
    KPartMeasureOpt,
)
from tests.Convert.Commands.CliProcess import CliProcess
from tests.Convert.Solidworks.PlainWriting.LeaseMeasPath import LeaseMeasPath
from tests.Convert.Solidworks.PlainWriting.MakeColdSource import MakeColdSource


# ordinary cli conversion must reach the exact measured cold route already accepted by the sdk
@MarkTests.parametrize("RoleName", ("Skew", "Step"))
def TestColdCli(TmpPath: FilePath, RoleName: str) -> None:
    Source, Envelope, Digest, NameValue = MakeColdSource(TmpPath, RoleName)
    Receipt = TmpPath / "Measurement.json"
    _ = Receipt.write_text(DumpJson(Envelope), encoding="utf-8")
    SdkTarget = BytesIO()
    SdkResult = ConvertFile(
        Source,
        SdkTarget,
        DestFormat=KPartFormatId,
        AllowCarrier=False,
        WriteValues={
            "final_destination": rf"C:\KitSdkCandidates\{NameValue}",
            KPartMeasureOpt: Envelope,
        },
    )
    assert SdkResult.vendor_loadable
    assert SdkResult.application_usable
    assert CalcSha(SdkTarget.getvalue()).hexdigest() == Digest
    with LeaseMeasPath(TmpPath, NameValue) as Target:
        Outcome = CliProcess(
            TmpPath,
            "convert",
            str(Source),
            str(Target),
            "--json",
            "--native-measurement",
            str(Receipt),
        )
        assert Outcome.returncode == 0, Outcome.stdout + Outcome.stderr
        Report = LoadJson(Outcome.stdout)
        assert Report["vendor_loadable"] is Report["application_usable"] is True
        assert Report["dropped"] == []
        assert Target.read_bytes() == SdkTarget.getvalue() == Source.read_bytes()
    assert CalcSha(Source.read_bytes()).hexdigest() == Digest
