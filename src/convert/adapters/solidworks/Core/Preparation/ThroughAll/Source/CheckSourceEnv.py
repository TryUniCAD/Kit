from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.ReadSourceTree import (
    ReadSourceTree,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.CheckSrcNames import (
    CheckSrcNames,
)
from interchange.document.Models.DocumentModel import CadDocument


# geometry projection must not use a partial or stripped source as proof of complete source ownership
def CheckSourceEnv(DocumentValue: CadDocument) -> None:
    DocumentValue.assert_valid()
    if (
        DocumentValue.source.format_id != "solidworks.sldprt"
        or DocumentValue.source.container_version != "4"
        or DocumentValue.assembly is not None
        or DocumentValue.DrawingValue is not None
        or DocumentValue.diagnostics
        or DocumentValue.materials
    ):
        raise ValueError("source owners require an ordinary resolved native part")
    _ = ReadSourceTree(DocumentValue)
    CheckSrcNames(DocumentValue)
    if (
        len(DocumentValue.configurations) != 1
        or not DocumentValue.configurations[0].active
        or DocumentValue.configurations[0].parent_id is not None
        or DocumentValue.configurations[0].overrides
        or DocumentValue.configurations[0].suppressed_feature_ids
        or len(DocumentValue.bodies) != 1
    ):
        raise ValueError(
            "source owners require one actual active configuration and body"
        )
