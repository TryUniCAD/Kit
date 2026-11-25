from dataclasses import replace

from EncoderRoundTrip.Artifacts import DOCUMENT_LIMIT, canonical_json, digest, read_record


def decode_document(content, format_id):
    from convert import open_document
    from interchange.document.Models.DocumentModel import CadDocument

    if format_id == "solidworks.sldprt":
        from convert.adapters.solidworks.Container.Container import SldprtArchive
        from convert.adapters.solidworks.Container.Format import KitDocStream

        if SldprtArchive.from_bytes(content, "<memory>").get(KitDocStream) is not None:
            raise ValueError("embedded Kit documents do not provide independent native source evidence")
    document = open_document(content, source_format=format_id, strict=True)
    if document.source.format_id != format_id or document.source.sha256 != digest(content):
        raise ValueError("SDK document does not bind the selected native format and bytes")
    document, comparison = _without_source_archive(document, content)
    document.assert_valid()
    neutral = canonical_json(document.to_dict())
    if len(neutral) > DOCUMENT_LIMIT:
        raise ValueError("neutral document exceeds 64 MiB")
    rebuilt = CadDocument.from_json(neutral.decode("utf-8"))
    rebuilt.assert_valid()
    if canonical_json(rebuilt.to_dict()) != neutral:
        raise ValueError("neutral JSON changed during typed reconstruction")
    if comparison is not None:
        key, archive = comparison
        from interchange.Core.Common import FreezeMapping

        rebuilt = replace(rebuilt, metadata=FreezeMapping({**rebuilt.metadata, key: archive}))
    return rebuilt, neutral, comparison is not None


def _without_source_archive(document, content):
    if document.source.format_id != "solidworks.sldprt":
        return document, None
    from convert.adapters.solidworks.Core.Adapter import KSourceBytesKey
    from interchange.Core.Common import FreezeMapping

    if KSourceBytesKey not in document.metadata:
        return document, None
    metadata = dict(document.metadata)
    archive = metadata.pop(KSourceBytesKey)
    if type(archive) is not bytes or archive != content:
        raise ValueError("SDK-retained comparison archive differs from the native source")
    return replace(document, metadata=FreezeMapping(metadata)), (KSourceBytesKey, archive)


def _check_writer_wire(wire):
    pending = [wire]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            if "$bytes" in value or "solidworks_source_bytes" in value:
                raise ValueError("prepared writer document retains a native byte payload")
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)


def encode_writer_input(document):
    from interchange.document.Models.DocumentModel import CadDocument

    if type(document) is not CadDocument:
        raise TypeError("prepared writer input must be a CadDocument")
    document.assert_valid()
    wire = document.to_dict()
    _check_writer_wire(wire)
    encoded = canonical_json(wire)
    if len(encoded) > DOCUMENT_LIMIT:
        raise ValueError("prepared writer document exceeds 64 MiB")
    return encoded


def decode_writer_input(payload, format_id, source_sha256):
    from interchange.document.Models.DocumentModel import CadDocument

    try:
        wire = read_record(payload)
    except (OverflowError, RecursionError, TypeError, ValueError) as error:
        raise ValueError("prepared writer document is not valid JSON") from error
    _check_writer_wire(wire)
    try:
        document = CadDocument.from_dict(wire)
        canonical = canonical_json(document.to_dict())
        source = document.source.format_id, document.source.sha256
    except (AttributeError, KeyError, OverflowError, RecursionError, TypeError, ValueError) as error:
        raise ValueError("prepared writer document is not a valid CadDocument") from error
    if canonical != payload:
        raise ValueError("prepared writer document changed during typed reconstruction")
    if source != (format_id, source_sha256):
        raise ValueError("prepared writer document source does not match the round-trip source")
    return document
