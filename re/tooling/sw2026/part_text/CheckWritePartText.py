from functools import partial
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PartTextProbe import check_model, model_state, read_part, refuse_write
from convert import convert, open_document, write_document
from convert.adapters.base.ReadOptions import ReadOptions
from convert.api.ApiContext import GetRegistry
from convert.engine.EngineConvert import EngineConvert

CAUSE = "part properties require an empty compatible native manager"


def check_neutral_copy(document, legacy):
    expected = model_state(document)
    source = document.to_json().encode()
    first, second = BytesIO(), BytesIO()
    convert(source, first, source_format="interchange.json", destination_format="interchange.json",
            allow_carrier=False)
    legacy.ConvertData(source, second, SourceFormat="interchange.json", DestFormat="interchange.json")
    result = {}
    for mode, stream in (("ordinary", first), ("compatibility", second)):
        restored = open_document(stream.getvalue(), source_format="interchange.json", strict=True)
        check_model(document, restored)
        observed = model_state(restored)
        if (expected != observed or document.source != restored.source
                or document.diagnostics != restored.diagnostics or document.configurations != restored.configurations
                or document.brep_payloads != restored.brep_payloads or document.meshes != restored.meshes):
            raise ValueError("neutral JSON copy changed the original native inspection state")
        result[mode] = observed["status"]
    return result


def check_filtered_copy(document):
    source = document.to_json().encode()
    options = {"source_format": "interchange.json", "destination_format": "interchange.json"}
    restrictions = {"geometry": {"include_brep": False}, "mesh": {"include_tessellation": False},
                    "configuration": {"configuration": document.configurations[0].name}}
    return {name: refuse_write(partial(convert, source, **options, **selected), CAUSE)
            for name, selected in restrictions.items()}


def inspect(source):
    document = read_part(source)
    relaxed = read_part(source, strict=False)
    check_model(document, relaxed)
    state = model_state(document)
    if state != model_state(relaxed):
        raise ValueError("nonstrict inspection changed the explicit property refusal")
    registry = GetRegistry()
    legacy = EngineConvert()
    legacy.registry = registry
    options = {
        "source_format": "solidworks.sldprt",
        "destination_format": "interchange.json",
        "include_tessellation": False,
    }
    operations = {
        "strict": partial(convert, source, **options),
        "nonstrict": partial(convert, source, strict=False, **options),
        "public_write": partial(
            write_document, relaxed, destination_format="interchange.json",
            validate=False, allow_carrier=True,
        ),
        "registry": partial(registry.write, relaxed, format_id="interchange.json"),
        "compatibility": partial(
            legacy.ConvertData, source, SourceFormat="solidworks.sldprt",
            DestFormat="interchange.json", ReadOpts=ReadOptions(
                strict=False, include_tessellation=False,
            ),
        ),
    }
    refusals = {name: refuse_write(call, CAUSE) for name, call in operations.items()}
    with TemporaryDirectory(prefix="KitRefusedPartText") as scratch:
        destination = Path(scratch) / "part.json"
        try:
            write_document(relaxed, destination)
        except ValueError as error:
            if str(error) != refusals["public_write"] or any(Path(scratch).iterdir()):
                raise ValueError("implicit path refusal changed its destination") from error
        else:
            raise ValueError("implicit path published unsupported text")
    state["source_sha256"] = sha256(source.read_bytes()).hexdigest()
    state["refusals"] = refusals
    state["implicit_path_unchanged"] = True
    state["neutral_copies"] = check_neutral_copy(document, legacy)
    state["filtered_copies_refused"] = check_filtered_copy(document)
    return state


if __name__ == "__main__":
    print(json.dumps(inspect(Path(sys.argv[1])), sort_keys=True))
