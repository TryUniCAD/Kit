from hashlib import sha256 as CalcSha
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from pytest import mark as MarkTests

from tests.Convert.Commands.CliProcess import CliProcess
from tests.Convert.Solidworks.PlainWriting.LeaseMeasPath import LeaseMeasPath
from tests.Convert.Solidworks.PlainWriting.MakeColdSource import MakeColdSource


# cold readback parity must preserve exact receipt matching and transactional destination refusal
@MarkTests.parametrize("RoleName", ("Skew", "Step"))
@MarkTests.parametrize("ReceiptMode", ("missing", "stale"))
def TestColdReceipt(TmpPath: FilePath, RoleName: str, ReceiptMode: str) -> None:
    Source, Envelope, Digest, NameValue = MakeColdSource(TmpPath, RoleName)
    Receipt = TmpPath / "Measurement.json"
    Arguments: tuple[str, ...] = ()
    if ReceiptMode == "stale":
        Record = CastValue(dict[str, object], LoadJson(DumpJson(Envelope)))
        Evidence = CastValue(dict[str, object], Record["receipt"])
        Evidence["cases"] = [
            Entry
            for Entry in CastValue(list[dict[str, object]], Evidence["cases"])
            if Entry["role"] != RoleName
        ]
        _ = Receipt.write_text(DumpJson(Record), encoding="utf-8")
        Arguments = ("--native-measurement", str(Receipt))
    with LeaseMeasPath(TmpPath, NameValue) as Target:
        _ = Target.write_bytes(b"preserved destination")
        Outcome = CliProcess(
            TmpPath,
            "convert",
            str(Source),
            str(Target),
            "--json",
            "--overwrite",
            *Arguments,
        )
        assert Outcome.returncode == 1 and not Outcome.stdout
        assert (
            "no unique exact native measurement"
            if ReceiptMode == "stale"
            else "publication requires an offline native measurement receipt"
        ) in Outcome.stderr
        assert Target.read_bytes() == b"preserved destination"
    assert CalcSha(Source.read_bytes()).hexdigest() == Digest
