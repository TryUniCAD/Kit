from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumDocument import Severity


# independently decoded configuration rows must stay visible beside the remaining resolved field boundary
def CheckCircleInfo(Document: CadDocument) -> None:
    (TypedInfo,) = Document.diagnostics
    PropertyInfo = CastValue(
        Mapping[str, object], Document.metadata["solidworks.part_text_properties"]
    )
    assert PropertyInfo["status"] == "complete"
    assert PropertyInfo["archive_version"] == KConfigGen
    assert PropertyInfo["configuration_ids"] == (0,)
    ManagerInfo = CastValue(
        Mapping[str, object],
        Document.metadata["solidworks.typed_configuration_manager"],
    )
    ConfigInfo = CastValue(
        Mapping[str, object], Document.metadata["solidworks.typed_configuration_graph"]
    )
    ResolvedInfo = CastValue(
        Mapping[str, object], Document.metadata["solidworks.typed_resolved_semantics"]
    )
    for InfoValue, StartValue, EndValue in ((ManagerInfo, 1, 17), (ConfigInfo, 4, 106)):
        assert InfoValue["status"] == "complete"
        assert InfoValue["archive_version"] == KConfigGen
        assert (InfoValue["map_base"], InfoValue["map_counter"]) == (
            StartValue,
            EndValue,
        )
        assert InfoValue["full_linked_graph"] is False
    assert ResolvedInfo["status"] == "unsupported"
    assert ResolvedInfo["full_linked_graph"] is False
    assert ResolvedInfo["public_writer_qualified"] is False
    assert (
        ResolvedInfo["diagnostic"]
        == "unsupported SOLIDWORKS body class moSimpleSurfIdRep_c schema 1"
    )
    assert TypedInfo.code == "sldprt.native_record_unresolved"
    assert TypedInfo.severity == Severity.INFO
    assert (
        TypedInfo.message
        == f"typed resolved semantics unavailable: {ResolvedInfo['diagnostic']}"
    )
