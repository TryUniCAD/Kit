from io import BytesIO
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

from convert import open_document

PROPERTY_STATUS = "solidworks.part_text_properties"
PROPERTY_DIAGNOSTIC = "solidworks.part_text_properties_unavailable"
CIRCULAR_PROFILE_OWNER = "sldprt:feature:18 (solidworks.sldprt:ProfileFeature)"


def read_part(source, strict=True):
    return open_document(
        source, source_format="solidworks.sldprt", strict=strict,
        include_tessellation=False,
    )


def model_state(document):
    config, = document.configurations
    body, = document.bodies
    brep = document.brep
    if brep is None:
        raise ValueError("the property probe must retain modeled geometry")
    return {
        "status": document.metadata.get(PROPERTY_STATUS),
        "diagnostics": [
            (d.code, d.severity.value, d.message)
            for d in document.diagnostics
            if d.code == PROPERTY_DIAGNOSTIC
        ],
        "text_scopes": [
            "document_summary" in document.metadata,
            "custom_properties" in document.metadata,
            "custom_properties" in config.attributes,
        ],
        "configuration": [config.name, config.active, config.attributes["native_configuration_id"]],
        "body": [body.id, body.topology.solid_count, len(brep.bodies), sum(r.solid for r in brep.regions)],
        "feature_count": len(document.feature_timeline),
    }


def check_model(original, observed):
    if any(
        getattr(original, name) != getattr(observed, name)
        for name in (
            "brep", "bodies", "feature_timeline", "parameters", "sketches", "support_planes",
        )
    ):
        raise ValueError("the property case changed the modeled part")


def refuse_output(operation, expected, *witnesses):
    target = BytesIO(b"unchanged")
    target.seek(3)
    try:
        operation(target)
    except ValueError as error:
        if target.getvalue() != b"unchanged" or target.tell() != 3:
            raise ValueError("refused write mutated its destination") from error
        message = str(error)
        matches = (message.startswith(expected) and all(value in message for value in witnesses)
                   if witnesses else message == expected)
        if not matches:
            raise ValueError(f"unexpected write refusal {error}") from error
        return message
    raise ValueError("a refused case crossed the write boundary")


def refuse_write(operation, cause):
    expected = f"SOLIDWORKS part text properties are unavailable for writing ({cause})"
    return refuse_output(operation, expected)
