from hashlib import sha256 as CalcSha
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Commands.CliProcess import CliProcess
from tests.Convert.Solidworks.PlainWriting.LeaseMeasPath import LeaseMeasPath
from tests.Convert.Solidworks.PlainWriting.MeasurePlainDoc import MeasurePlainDoc
from tests.Convert.Solidworks.PlainWriting.RefuseMeasPath import RefuseMeasPath


# the installed command must publish the exact file that the native application qualified
def VerifyCliMeas(Folder: FilePath, RoleName: str) -> None:
    Document, Envelope, Digest = MeasurePlainDoc(RoleName)
    NameValue = f"{Document.metadata['name']}.SLDPRT"
    Source = Folder / "Neutral.json"
    ReceiptPath = Folder / "Measurement.json"
    _ = Source.write_text(Document.to_json(), encoding="utf-8")
    _ = ReceiptPath.write_text(DumpJson(Envelope), encoding="utf-8")
    with LeaseMeasPath(Folder, NameValue) as Target:
        Outcome = CliProcess(
            Folder,
            "convert",
            str(Source),
            str(Target),
            "--json",
            "--native-measurement",
            str(ReceiptPath),
        )
        assert Outcome.returncode == 0 and not Outcome.stderr, (
            Outcome.stdout + Outcome.stderr
        )
        Report = CastValue(dict[str, object], LoadJson(Outcome.stdout))
        Written = Target.read_bytes()
        assert Report["application_usable"] is Report["vendor_loadable"] is True
        assert Report["dropped"] == []
        assert Report["bytes_written"] == len(Written)
        assert CalcSha(Written).hexdigest() == Digest
        if Target.parent == Folder:
            assert set(Folder.iterdir()) == {Source, Target, ReceiptPath}
            return
        assert set(Target.parent.iterdir()) == {Target}
        assert set(Folder.iterdir()) == {Source, ReceiptPath}
    RefuseMeasPath(Source, Folder / NameValue, ReceiptPath)
