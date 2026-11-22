from functools import partial
from hashlib import sha256
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PartTextProbe import check_model, model_state, read_part, refuse_output, refuse_write
from convert import convert
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.Formats.CheckSourceText import CheckSourceText


def inspect(source_path):
    native = source_path.read_bytes()
    archive = SldprtArchive.from_bytes(native)
    version = ContainerMo(archive.streams)
    if version != 18000:
        raise ValueError("legacy property fixture changed archive version")
    original = read_part(source_path)
    options = {
        "source_format": "solidworks.sldprt",
        "destination_format": "interchange.json",
        "strict": True,
        "include_tessellation": False,
    }
    original_portability = refuse_output(
        partial(convert, source_path, **options),
        "unqualified SOLIDWORKS sketch support references", "sldprt:sketch:40",
    )
    streams = dict(archive.streams)
    name = "docProps/core.xml"
    closing = b"</cp:coreProperties>"
    if streams[name].count(closing) != 1:
        raise ValueError("missing legacy summary root")
    streams[name] = streams[name].replace(
        closing, b"<dc:title>Authored legacy text</dc:title>" + closing,
    )
    changed = BuildSldprt(streams, Template=native)
    inspected = read_part(changed)
    check_model(original, inspected)
    cause = "legacy SOLIDWORKS part contains authored summary text"
    authored_portability = refuse_output(
        partial(convert, changed, **options),
        "unqualified SOLIDWORKS sketch support references", "sldprt:sketch:40",
    )
    refusal = refuse_write(lambda _: CheckSourceText(inspected), cause)
    if source_path.read_bytes() != native:
        raise ValueError("legacy source changed")
    return {
        "source_sha256": sha256(native).hexdigest(),
        "archive_version": version,
        "original": model_state(original),
        "original_portability_refusal": original_portability,
        "authored_title": model_state(inspected),
        "authored_portability_refusal": authored_portability,
        "refusal": refusal,
    }


if __name__ == "__main__":
    print(json.dumps(inspect(Path(sys.argv[1])), sort_keys=True))
