from __future__ import annotations

# codec initialization must finish before construction because lazy imports would cross the access boundary
KCodec = """
from builders.Definition import (
    part_definition as NewPartDef,
    definition_stream as WritePartDef,
)
from convert.adapters.solidworks.Container.Container import (
    build_sldprt as BuildContainer,
    SldprtArchive as ArchiveFile,
)

CodecReg = NewRegistry()
FindCodec("utf-16-le")
FindCodec("latin-1")
AuditGuard.BeginBuild()
"""
