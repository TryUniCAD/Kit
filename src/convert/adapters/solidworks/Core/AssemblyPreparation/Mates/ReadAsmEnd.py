from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.AssemblyGroups.PlaneEndIn import (
    PlaneEndIn,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from interchange.assembly.MateEntity import MateEntity


# actual occurrence paths and child datum ids must determine endpoint ownership without saved selection payloads or guessed captions
def ReadAsmEnd(
    Value: MateEntity,
    RootId: str,
    Occurrences: Mapping[str, int],
    DatumAxes: Mapping[str, str],
) -> PlaneEndIn:
    RequireAsm(
        Value.owner_definition_id == RootId and str(Value.kind) == "plane",
        "mate entity requires its actual root owner and plane kind",
    )
    RequireAsm(
        not Value.selection_id
        and Value.frame is None
        and Value.radius is None
        and Value.provenance is None
        and not Value.attributes,
        "mate entity has unsupported frame selection or extension state",
    )
    RequireAsm(
        len(Value.instance_path) == 1
        and Value.instance_path[0] in Occurrences
        and Value.source_entity_id in DatumAxes,
        "mate endpoint must resolve its actual direct occurrence and child principal datum",
    )
    return PlaneEndIn(
        Occurrences[Value.instance_path[0]], DatumAxes[Value.source_entity_id]
    )
