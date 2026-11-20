from functools import partial
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PartTextProbe import check_model, model_state, read_part, refuse_write
from convert import convert, open_document
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive


def inspect(source_path):
    native = source_path.read_bytes()
    target = BytesIO()
    result = convert(
        source_path, target, source_format="solidworks.sldprt",
        destination_format="interchange.json", strict=True,
    )
    roundtrip = open_document(BytesIO(target.getvalue()), source_format="interchange.json")
    check_model(result.document, roundtrip)
    streams = SldprtArchive.from_bytes(native).streams
    name = "docProps/core.xml"
    closing = b"</cp:coreProperties>"
    if streams[name].count(closing) != 1:
        raise ValueError("missing legacy summary root")
    streams[name] = streams[name].replace(
        closing, b"<dc:title>Authored legacy text</dc:title>" + closing,
    )
    changed = BuildSldprt(streams, Template=native)
    inspected = read_part(changed)
    check_model(read_part(native), inspected)
    state = model_state(inspected)
    cause = "legacy SOLIDWORKS part contains authored summary text"
    refusal = refuse_write(partial(
        convert, changed, source_format="solidworks.sldprt",
        destination_format="interchange.json", include_tessellation=False,
    ), cause)
    return {
        "source_sha256": sha256(native).hexdigest(),
        "original": model_state(result.document),
        "output_bytes": len(target.getvalue()),
        "authored_title": state,
        "refusal": refusal,
    }


if __name__ == "__main__":
    print(json.dumps(inspect(Path(sys.argv[1])), sort_keys=True))
