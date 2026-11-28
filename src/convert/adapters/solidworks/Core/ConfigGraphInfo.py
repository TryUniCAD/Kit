from collections.abc import Mapping
from dataclasses import replace as ReplaceValue
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Config.ConfigGraph import ConfigGraph
from convert.adapters.solidworks.Archive.Config.DescribeConfig import DescribeConfig
from convert.adapters.solidworks.Archive.Config.ReadConfigInfo import ReadConfigInfo
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from interchange import CadDocument, Diagnostic, Severity, frozen_mapping as FrozenMapping


# the normal sdk must disclose its exact configuration grammar boundary without replacing legacy semantics
def WithConfigInfo(
    Document: CadDocument, Archive: SldprtArchive, GraphValue: ConfigGraph | None = None
) -> CadDocument:
    Metadata = dict(Document.metadata)
    VersionValue = ContainerMo(Archive.streams)
    BufferValue = Archive.get("Contents/Config-0")
    HeaderBuffer = Archive.get("Contents/Config-0-ModelHeader")
    ManagerInfo = CastValue(Mapping[str, object], Metadata.get("solidworks.typed_configuration_manager", {}))
    if GraphValue is not None:
        InfoValue = DescribeConfig(GraphValue, ManagerInfo)
    elif BufferValue is None or HeaderBuffer is None:
        InfoValue = {"status": "missing", "archive_version": VersionValue, "full_linked_graph": False}
    else:
        InfoValue = ReadConfigInfo(BufferValue, HeaderBuffer, VersionValue, ManagerInfo)
    Metadata["solidworks.typed_configuration_graph"] = InfoValue
    Diagnostics = Document.diagnostics
    if InfoValue["status"] == "unsupported":
        Diagnostics += (Diagnostic(code="solidworks.typed_configuration_graph_unavailable",
                                   message=str(InfoValue["diagnostic"]), severity=Severity.INFO),)
    return ReplaceValue(Document, metadata=FrozenMapping(Metadata), diagnostics=Diagnostics)
