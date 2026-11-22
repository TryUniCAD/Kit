from dataclasses import replace
from hashlib import sha256
from io import BytesIO
import os

from CheckScopedPlainWriter import reject


def require(value, message):
    if not value:
        raise ValueError(message)


def check_republish(target, audit, payload, receipt, epoch, locator, expected):
    from convert import open_document, write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter

    format_id = "solidworks.sldprt"
    values = {"solidworks_native_measurement": {"receipt": receipt, "written_at": epoch},
              "final_destination": locator, "require_native_transfers": True}
    writer = SldprtWriter()
    options = WriteOptions(values=values)
    readers = tuple(open_document(payload, source_format=format_id, strict=True, include_brep=geometry)
                    for geometry in (True, False))

    def registry(document, sink):
        return write_document(document, sink, destination_format=format_id, allow_carrier=False,
                              overwrite=True, values=values)

    def direct(document, sink):
        return writer.write(document, sink, options)

    exact = sha256(payload).hexdigest() == expected
    successes = path_writes = 0
    refusals = []
    opened = audit.target_opens
    audit.phase = "write"
    try:
        for document in readers:
            require(len(document.parameters) == 2
                    and PrepareNative(document, BytesIO(), epoch, options).BytesValue == payload,
                    "strict two-driver reread did not regenerate the same full archive")
            for emit in (direct, registry):
                sink = BytesIO()
                if exact:
                    outcome = emit(document, sink)
                    verify_publication(document, outcome, expected)
                    require(sink.getvalue() == payload, "published stream differs from its measured source")
                    successes += 1
                else:
                    reject(lambda: emit(document, sink), ValueError, "no unique exact native measurement")
                    require(not sink.getvalue(), "unmeasured compressor populated a stream")
            if exact and os.name != "nt":
                verify_publication(document, registry(document, target), expected)
                path_writes += 1
            else:
                reject(lambda: registry(document, target), ValueError, "no unique exact native measurement")

        original = readers[0]
        changed = replace(original, metadata={**original.metadata, "unmapped_circle_semantics": True})
        sink = BytesIO()
        for emit in (direct, registry):
            refusals.append(reject(lambda: emit(changed, sink), ValueError,
                                   "cold readback differs from its regenerated part"))
        require(not sink.getvalue() and audit.target_opens == opened + path_writes and not audit.denied,
                "writer accessed input or a refused reread touched an output")
    finally:
        audit.phase = "done"
    if path_writes:
        require(target.read_bytes() == payload, "path publication differs from its measured source")
    return {"strict_profiles": len(readers), "stream_publications": successes, "path_publications": path_writes,
            "exact_regeneration": True, "unrepresented_scope_refusals": refusals}


def verify_publication(document, result, expected):
    require(result.vendor_loadable and result.application_usable
            and result.metadata["solidworks_native_measurement"]["generated_sha256"] == expected
            and result.native_capabilities == document.capabilities,
            "strict reread publications lost exact native evidence or transfers")
