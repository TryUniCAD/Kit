from interchange.assembly.AssemblyEnums import ComponentKind
from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.document.Models.DocumentModel import (
    AssemblyData,
    CadDocument,
    ComponentDoc,
)
from interchange.Records.RecordSource import CadSource


# an ordinary assembly root must preserve the inspection restriction of its embedded native component
def NestReadOnly(Document: CadDocument) -> CadDocument:
    RootDef = ComponentDef("root", "assembly", ComponentKind.KAssembly)
    ChildDef = ComponentDef(
        "child", "native part", ComponentKind.KPart, document_id="nested"
    )
    Assembly = AssemblyData(
        RootDef.id,
        (RootDef, ChildDef),
        (ComponentInst("instance", "part", ChildDef.id, RootDef.id),),
        (ComponentDoc("nested", Document),),
    )
    return CadDocument(
        CadSource("interchange.json", "assembly.json", "0" * 64),
        (),
        (),
        (),
        (),
        (),
        (),
        (),
        assembly=Assembly,
    )
