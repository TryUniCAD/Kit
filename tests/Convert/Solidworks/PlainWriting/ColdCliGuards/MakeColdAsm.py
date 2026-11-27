from interchange.assembly.AssemblyEnums import ComponentKind
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.document.Models.DocumentModel import (
    AssemblyData,
    CadDocument,
    ComponentDoc,
)


# embedded native context must remain complete input rather than disappearing behind a cold root marker
def MakeColdAsm(Document: CadDocument, IsEmbedded: bool) -> AssemblyData:
    RootValue = ComponentDef("assembly/root", "Root", ComponentKind.KAssembly)
    if not IsEmbedded:
        return AssemblyData(RootValue.id, (RootValue,), ())
    ChildValue = ComponentDef(
        "assembly/part", "Part", ComponentKind.KPart, document_id="document/part"
    )
    Instance = ComponentInst("instance/part", "Part", ChildValue.id, RootValue.id)
    return AssemblyData(
        RootValue.id,
        (RootValue, ChildValue),
        (Instance,),
        (ComponentDoc("document/part", Document),),
    )
