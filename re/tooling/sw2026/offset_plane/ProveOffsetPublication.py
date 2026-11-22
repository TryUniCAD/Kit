from dataclasses import replace
from io import BytesIO

from convert import write_document
from convert.adapters.base.GetDocumentCaps import GetDocumentCaps
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from convert.adapters.solidworks.Core.Writing.OffsetPlanes.OffsetOptions import (
    KOffsetWriteOpt,
    OffsetOptions,
)
from interchange.document.Models.DocumentModel import CadDocument


FORMAT = "solidworks.sldprt"
MEASUREMENT = "solidworks_native_measurement"


def publish_public(document, sink, values):
    return write_document(
        document, sink, destination_format=FORMAT, allow_carrier=False, values=values
    )


def publish_direct(document, sink, values):
    return SldprtWriter().write(document, sink, WriteOptions(values=values))


def publish_adapter(document, sink, values):
    return SldprtAdapter().write(document, sink, WriteOptions(values=values))


def refuse(route, document, values, expected):
    sink = BytesIO(b"independent destination contents")
    sink.seek(4)
    try:
        route(document, sink, values)
    except ValueError as error:
        if expected not in str(error):
            raise
    else:
        raise RuntimeError("invalid measurement crossed the offset publication gate")
    if sink.tell() != 4 or sink.getvalue() != b"independent destination contents":
        raise ValueError("refused offset publication modified the destination")


def prove(document, recipe, text, event, report_text, expected_bytes, expected_digest):
    rules = OffsetOptions(recipe, text)
    measurement = {"written_at": event, "receipt": {"native_report": report_text}}
    options = {
        "final_destination": recipe.OutputValue.PathName,
        "require_native_transfers": True,
        KOffsetWriteOpt: rules,
        MEASUREMENT: measurement,
    }
    copies = (document, CadDocument.from_json(document.to_json(indent=None)))
    variations = (
        ({key: value for key, value in options.items() if key != MEASUREMENT}, "offline native measurement"),
        ({key: value for key, value in options.items() if key != KOffsetWriteOpt}, "authored part and radial presentation"),
        ({**options, MEASUREMENT: {**measurement, "receipt": {"native_report": report_text + " "}}}, "authenticated offline evidence"),
        ({**options, MEASUREMENT: {**measurement, "written_at": event + 1}}, "creation epochs"),
        ({**options, "final_destination": "C:\\UnmeasuredOffset.SLDPRT"}, "exact authored locator"),
        ({**options, KOffsetWriteOpt: replace(rules, RadialTextPoint=(text[0] + 0.002, text[1]))}, "no matching native measurement"),
    )
    caps = GetDocumentCaps(document)
    result = {}
    for route in (publish_public, publish_direct, publish_adapter):
        for model in copies:
            sink = BytesIO()
            report = route(model, sink, options)
            if (
                sink.getvalue() != expected_bytes
                or not report.vendor_loadable
                or not report.application_usable
                or not caps <= report.native_capabilities
                or report.dropped
                or report.carrier_capabilities
                or report.metadata[MEASUREMENT]["generated_sha256"] != expected_digest
            ):
                raise ValueError("normal offset publication contradicts the exact scoped candidate")
        for bad, reason in variations:
            refuse(route, document, bad, reason)
        result[route.__name__] = {"whole_streams": len(copies), "refusals": len(variations)}
    return result
