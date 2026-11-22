from codecs import lookup
from contextlib import redirect_stdout
from gzip import decompress
from importlib import import_module
from io import BytesIO, StringIO
from json import dumps, loads
from pathlib import Path
from platform import machine
import sys
from tempfile import TemporaryDirectory
from zlib import ZLIB_RUNTIME_VERSION

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path.insert(0, str(HERE.parent))

from ProveMainAttachedBox import Audit, FORMAT, OUTPUT_SHA, SOURCE_SHA
from ProveMainAttachedBox import check_source_evidence, digest, inspect_box, read_locked
from convert import open_document, write_document
from convert.Commands.PrintReport import PrintReport
from convert.Commands.WriteReport import WriteReport
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Preparation.FreecadBox.PrepareBoxAxes import PrepareBoxAxes
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter

FIXTURE = ROOT / "re/solidworks/v2026/corpus/freecad/MeasuredF14c01"
LOCATOR = r"C:\KitAttachedBoxAxes01\F14c.SLDPRT"
MEASUREMENT = "solidworks_native_measurement"


def verify(scratch):
    source = read_locked(FIXTURE / "F14c.FCStd", SOURCE_SHA)
    measure = decompress((FIXTURE / "Measurement.json.gz").read_bytes())
    assert digest(measure) == "35799ebe49e0b7a39673b65c3ef701577492c02d2df48c95706678bcc29062cd"
    options = {MEASUREMENT: loads(measure), "require_native_transfers": True, "final_destination": LOCATOR}
    document = open_document(source, source_format="freecad.fcstd", strict=True)
    for codec in ("utf-8", "utf-8-sig", "utf-16-le", "latin-1", "cp1252"):
        lookup(codec)
    import_module("interchange.brep.Validation.BrepValidate")
    import_module("interchange.document.Models.DocumentProvenance")
    known_runtime = (sys.platform, machine(), sys.version_info[:3], ZLIB_RUNTIME_VERSION) in (
        ("darwin", "arm64", (3, 14, 7), "1.2.12"),
        ("win32", "ARM64", (3, 12, 7), "1.3.1"),
    )
    audit = Audit(scratch)
    attempts = []
    writer = SldprtWriter()
    for registry in (True, False):
        preparations = 0
        sink = BytesIO()

        def profile(frame, event, _):
            nonlocal preparations
            if event == "call" and frame.f_code is PrepareBoxAxes.__code__:
                preparations += 1

        def send():
            if registry:
                return write_document(document, sink, destination_format=FORMAT, values=options, allow_carrier=False)
            return writer.write(document, sink, WriteOptions(values=options))

        sys.setprofile(profile)
        try:
            try:
                result = audit.run(send)
            except ValueError as error:
                assert not known_runtime and "differs from the measured whole archive" in str(error), error
                assert not sink.getvalue() and sink.tell() == 0
                result = None
        finally:
            sys.setprofile(None)
        assert preparations == 1
        if result is not None:
            raw = sink.getvalue()
            assert digest(raw) == OUTPUT_SHA and len(raw) == 10707
            check_source_evidence(result)
            printed = StringIO()
            payload = {"source_format": "freecad.fcstd", "destination_format": FORMAT, **WriteReport(result)}
            with redirect_stdout(printed):
                PrintReport(payload)
            line, = (row for row in printed.getvalue().splitlines() if row.startswith("source_evidence: "))
            assert loads(line.removeprefix("source_evidence: ")) == payload["source_evidence"]
            for full in (True, False):
                parsed = audit.run(lambda: open_document(raw, source_format=FORMAT, strict=True, include_brep=full))
                inspect_box(parsed, full)
        attempts.append({"registry": registry, "preparation_count": preparations, "exact_publication": result is not None})
    assert attempts[0]["exact_publication"] == attempts[1]["exact_publication"]
    return {"attempts": attempts, "known_runtime": known_runtime, "result": audit.result()}


if __name__ == "__main__":
    with TemporaryDirectory(prefix="KitMeasuredF14c-") as area:
        print(dumps(verify(Path(area).resolve()), sort_keys=True))
