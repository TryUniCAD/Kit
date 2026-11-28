from base64 import b64encode
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
from json import dumps, loads
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]


def invalid_intents(document, options, written_at, prepare):
    datum, boss = document.feature_timeline
    offset, radial, depth = document.parameters
    variants = (
        (
            replace(
                document,
                parameters=(
                    replace(
                        offset,
                        value=replace(offset.value, value=offset.value.value * 1.5),
                    ),
                    radial,
                    depth,
                ),
            ),
            "offset definition and its positive driving D1 disagree",
        ),
        (
            replace(
                document, feature_timeline=(datum, replace(boss, input_feature_ids=()))
            ),
            "offset plane part requires its ordered datum sketch and boss",
        ),
        (
            replace(document, metadata={**document.metadata, "unmodeled": True}),
            "plain boss candidate does not admit unprojected document metadata",
        ),
    )
    failures = []
    for variant, expected in variants:
        sink = BytesIO(b"independent sink state")
        sink.seek(4)
        try:
            prepare(variant, sink, written_at, options)
        except ValueError as error:
            if expected not in str(error):
                raise
        else:
            raise ValueError("unsupported neutral model crossed offset preparation")
        if sink.getvalue() != b"independent sink state" or sink.tell() != 4:
            raise ValueError("invalid model changed the supplied destination")
        failures.append(expected)
    return failures


def build(request):
    sys.path.insert(0, str(ROOT / "src"))
    sys.path.insert(0, str(ROOT / "re/tooling/sw2026"))
    from CheckScopedPlainWriter import WriterAudit
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Archive.Header.ReadFileTable import GetFileRef
    from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import (
        ReadHeaderGraph,
    )
    from convert.adapters.solidworks.Core.Preparation.OffsetPlane.PrepareOffPart import (
        PrepareOffPart,
    )
    from interchange.document.Models.DocumentModel import CadDocument

    if set(request) != {"document", "final_destination", "written_at"}:
        raise ValueError(
            "isolated SDK offset worker takes only neutral design, locator, and event"
        )
    document = CadDocument.from_json(dumps(request["document"], allow_nan=False))
    written_at = request["written_at"]
    locator = request["final_destination"]
    if type(written_at) is not int or not 0 <= written_at <= 0xFFFFFFFF:
        raise ValueError("invalid creation event")
    options = WriteOptions(values={"final_destination": locator})
    for module_name in (
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
    ):
        import_module(module_name)
    for encoding in ("utf-8", "utf-16-le", "latin-1", "ascii"):
        lookup(encoding)
    audit = WriterAudit(ROOT / "src", ROOT / "unused-offset-datum.SLDPRT")
    sys.addaudithook(audit.observe)
    audit.phase = "write"
    candidate = PrepareOffPart(document, BytesIO(), written_at, options)
    refusals = invalid_intents(document, options, written_at, PrepareOffPart)
    audit.phase = "done"
    if (
        audit.target_opens
        or audit.denied
        or any(
            name in sys.modules
            for name in ("pythoncom", "win32com.client", "FreeCAD", "adsk")
        )
    ):
        raise ValueError("isolated SDK offset process crossed its runtime boundary")
    header_value = ReadHeaderGraph(
        candidate.StreamsValue["Contents/Config-0-ModelHeader"], 19000
    )
    locator_value = GetFileRef(header_value.FieldsValue["f38"])
    if locator_value.PathValue != locator:
        raise ValueError("SDK offset embedded final locator differs")
    data = candidate.BytesValue
    return {
        "data": b64encode(data).decode("ascii"),
        "sha256": sha256(data).hexdigest(),
        "bytes": len(data),
        "streams": len(candidate.StreamsValue),
        "file_reads": len(audit.denied),
        "neutral_refusals": refusals,
    }


if __name__ == "__main__":
    print(dumps(build(loads(sys.stdin.buffer.read())), sort_keys=True))
