from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from io import BytesIO
from json import dumps
from pathlib import Path, PureWindowsPath
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from interchange.document.Models.DocumentModel import CadDocument


def digest(value):
    return sha256(value).hexdigest()


def construct(document, locator, epoch):
    for value in ("ascii", "latin-1", "cp1252", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(value)
    blocked = []
    active = True

    def audit(event, _):
        if active and (
            event in ("open", "os.listdir", "os.scandir", "os.system", "os.exec",
                      "os.posix_spawn", "os.startfile", "os.fork")
            or event.startswith(("subprocess.", "socket.", "ctypes.", "winreg."))
        ):
            blocked.append(event)
            raise RuntimeError("native preparation attempted external access: " + event)

    settings = WriteOptions(values={"final_destination": str(locator)})
    sys.addaudithook(audit)
    try:
        candidate = PrepareNative(document, BytesIO(), epoch, settings)
    finally:
        active = False
    if blocked:
        raise RuntimeError("native preparation requested external input")
    return candidate


def gather(args):
    locator = PureWindowsPath(args.native_locator)
    if not locator.is_absolute() or locator.suffix.casefold() != ".sldprt":
        raise ValueError("the measurement candidate needs its actual absolute Windows part locator")
    scratch = args.scratch.resolve()
    if scratch.is_relative_to(ROOT / "src"):
        raise ValueError("candidate evidence belongs outside the source tree")
    if scratch.exists():
        raise ValueError("prepare into a fresh scratch directory")
    text = args.neutral.read_bytes()
    document = CadDocument.from_json(text.decode("utf-8"))
    candidate = construct(document, locator, args.written_at)
    raw = candidate.BytesValue
    receipt = {
        "schema": "kit.sw2026.plain-part-measurement-input.v1",
        "stage": "awaiting_native_measurement",
        "neutral_sha256": digest(text),
        "archive_sha256": digest(raw),
        "archive_bytes": len(raw),
        "runtime_input_reads": 0,
        "native_locator": str(locator),
        "written_at": args.written_at,
        "streams": {name: [len(data), digest(data)] for name, data in candidate.StreamsValue.items()},
    }
    scratch.mkdir(parents=True, exist_ok=False)
    with (scratch / locator.name).open("xb") as output:
        output.write(raw)
    frame = (dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")
    with (scratch / "Candidate.json").open("xb") as output:
        output.write(frame)
    return {"candidate_sha256": receipt["archive_sha256"], "manifest_sha256": digest(frame)}


if __name__ == "__main__":
    parser = ArgumentParser(description="Prepare a neutral SOLIDWORKS part for a separate native measurement")
    parser.add_argument("--neutral", required=True, type=Path)
    parser.add_argument("--native-locator", required=True)
    parser.add_argument("--written-at", required=True, type=int)
    parser.add_argument("--scratch", required=True, type=Path)
    print(dumps(gather(parser.parse_args()), sort_keys=True))
