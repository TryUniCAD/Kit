from typing import cast as CastValue

from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.Records.RecordConfig import Configuration


# every direct occurrence must retain complete configuration ownership and the measured visible rigid unsuppressed state
def CheckAsmOcc(
    Value: ComponentInst,
    RootValue: ComponentDef,
    ChildValue: ComponentDef,
    ChildConfig: Configuration,
) -> None:
    RequireAsm(
        Value.owner_definition_id == RootValue.id
        and Value.definition_id == ChildValue.id,
        "occurrence does not own the same direct dependency",
    )
    RequireAsm(
        (Value.configuration_name, Value.configuration_id)
        == (ChildConfig.name, ChildConfig.id),
        "occurrence selected configuration differs",
    )
    FlagsValue = (
        Value.suppressed,
        Value.hidden,
        Value.flexible,
        Value.exclude_from_bom,
    )
    RequireAsm(
        all(
            type(CastValue(object, FlagValue)) is bool and not FlagValue
            for FlagValue in FlagsValue
        )
        and type(CastValue(object, Value.fixed)) is bool,
        "occurrence requires exact visible rigid unsuppressed boolean state",
    )
    RequireAsm(
        not Value.reference_number
        and Value.provenance is None
        and not Value.attributes,
        "occurrence has unsupported reference or extension state",
    )
