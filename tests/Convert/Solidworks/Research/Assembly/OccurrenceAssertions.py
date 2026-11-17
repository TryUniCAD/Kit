from __future__ import annotations

from typing import cast as CastValue

from tests.Convert.Solidworks.Research.Assembly.AssemblyRootTests import KAssemblyRoots


# generated topology must retain the native stream boundaries and one active occurrence
def CheckOccReport(Report: dict[str, object]) -> None:
    assert Report["native_acceptance"] is False and Report["denied_reads"] == []
    assert Report["resolved_types"] == KAssemblyRoots
    assert Report["component_total"] == Report["configuration_component_total"] == 1
    assert Report["header_component_totals"] == [1, 1]
    assert Report["configuration_self_first"] is True
    assert Report["reconstructed_bytes_identical"] is Report["maps_consistent"] is True
    assert (
        Report["manager_bytes_identical"] is Report["resolved_bytes_identical"] is True
    )
    assert Report["empty_mates_linked"] is Report["definition_bytes_identity"] is True
    assert all(CastValue(dict[str, bool], Report["metadata_roundtrips"]).values())


# directory timestamps and file identity come from the independently generated child
def CheckDirectory(Report: dict[str, object]) -> object:
    assert Report["directory_slots"] == [4]
    assert Report["directory_headers_agree"] is True
    (DirectoryEntry,) = CastValue(list[dict[str, object]], Report["directory"])
    Child = CastValue(dict[str, object], Report["child"])
    ChildFile = CastValue(dict[str, object], Child["self_reference"])
    DirectoryFields = CastValue(dict[str, int], DirectoryEntry["record"])
    ChildFields = CastValue(dict[str, int], ChildFile["record"])
    ChildHeader = CastValue(dict[str, int], Child["configuration_manager_header"])
    assert DirectoryEntry["path"] == ChildFile["path"]
    assert DirectoryEntry["configuration"] == {"f08": "", "f10": -1}
    assert DirectoryFields["f48"] == 1 and DirectoryFields["f78"] == 0
    assert DirectoryFields["f60"] == ChildFields["f60"]
    assert DirectoryFields["f70"] == ChildHeader["saved_at"]
    return ChildFile["configuration"]


# the configuration path and model occurrence join through the persistent feature id
def CheckReference(Report: dict[str, object], ChildConfig: object) -> dict[str, object]:
    (Reference,) = CastValue(list[dict[str, object]], Report["occurrences"])
    (Option,) = CastValue(list[dict[str, object]], Report["occurrence_configurations"])
    assert Reference["ordinal"] == len(KAssemblyRoots) - 1
    assert Reference["name"] == Option["name"] == "GeneratedChildModel-1"
    assert (
        Reference["child_configuration"] == Option["child_configuration"] == ChildConfig
    )
    assert Reference["id"] == Option["feature_id"]
    assert Reference["has_backlink"] is True
    assert Option["has_backlink"] is Option["has_serialized_owner"] is False
    assert Option["parent_identity_shared"] is True
    assert Option["chain_count"] == 1 and Option["chain_mode"] == 0
    UpdateStamps = CastValue(dict[str, int], Reference["update_stamps"])
    assert Option["chain_stamp"] == 101 + UpdateStamps["f3f0"]
    return Reference
