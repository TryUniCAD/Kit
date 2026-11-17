from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrInfo import ReadCmgrInfo
from convert.adapters.solidworks.Core.ConfigGraphInfo import WithConfigInfo
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from interchange import CadDocument, Diagnostic, Severity, frozen_mapping as FrozenMapping


# normal sdk reads must expose typed configuration evidence while preserving older semantic projections
def WithCmgrInfo(Document: CadDocument, Archive: SldprtArchive) -> CadDocument:
    Metadata = dict(Document.metadata)
    VersionValue = ContainerMo(Archive.streams)
    BufferValue = Archive.get("Contents/CMgr")
    InfoValue = (
        {"status": "missing", "archive_version": VersionValue, "full_linked_graph": False}
        if BufferValue is None else ReadCmgrInfo(BufferValue, VersionValue)
    )
    Metadata["solidworks.typed_configuration_manager"] = InfoValue
    Diagnostics = Document.diagnostics
    if InfoValue["status"] == "unsupported":
        Diagnostics += (Diagnostic(
            code="solidworks.typed_configuration_manager_unavailable",
            message=str(InfoValue["diagnostic"]), severity=Severity.INFO,
        ),)
    return WithConfigInfo(ReplaceValue(Document, metadata=FrozenMapping(Metadata), diagnostics=Diagnostics), Archive)
