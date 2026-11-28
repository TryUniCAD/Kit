from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from interchange.assembly.ComponentDefinition import ComponentDef


# source references and cached extras cannot substitute for complete owned portable dependencies at this boundary
def CheckAsmDef(Definition: ComponentDef) -> None:
    RequireAsm(
        Definition.bounding_box is None
        and not Definition.mesh_ids
        and not Definition.source_path
        and not Definition.source_format_id
        and not Definition.source_sha256,
        "definition has unsupported cached geometry or external source references",
    )
    RequireAsm(
        Definition.provenance is None and not Definition.attributes,
        "definition has unprojected provenance or attributes",
    )
