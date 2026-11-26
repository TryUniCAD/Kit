from functools import partial
from hashlib import sha256
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PartTextProbe import model_state, read_part, refuse_output
from convert import open_document, write_document


def text_bags(document):
    configuration, = document.configurations
    return [document.metadata["document_summary"], document.metadata["custom_properties"],
            configuration.attributes["custom_properties"]]


def inspect(source):
    raw = source.read_bytes()
    original = read_part(source)
    restored = open_document(original.to_json().encode("utf-8"), source_format="interchange.json",
                             strict=True, include_tessellation=False)
    if restored != original:
        raise ValueError("JSON inspection changed the full native inspection document")
    state, text = model_state(restored), text_bags(restored)
    refusal = {
        name: refuse_output(
            partial(write_document, original, destination_format="interchange.json", allow_carrier=carrier),
            "native-only feature definitions cannot be exported",
            "sldprt:feature:-1", "Sheet-Metal Master",
        )
        for name, carrier in (("without_carrier", False), ("with_carrier", True))
    }
    if source.read_bytes() != raw:
        raise ValueError("disclosed circular control changed")
    return {
        "source_sha256": sha256(raw).hexdigest(),
        "status": state["status"],
        "text": text,
        "configuration": state["configuration"],
        "source_provenance_preserved": True,
        "direct_portability_refusals": refusal,
    }


if __name__ == "__main__":
    print(json.dumps(inspect(Path(sys.argv[1])), sort_keys=True))
