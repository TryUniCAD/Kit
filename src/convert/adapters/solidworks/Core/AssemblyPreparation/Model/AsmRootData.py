from dataclasses import dataclass as DataClass

from interchange.assembly.ComponentDefinition import ComponentDef
from interchange.assembly.ComponentInstance import ComponentInst
from interchange.assembly.MateGroup import MateGroup
from interchange.document.Models.DocumentModel import AssemblyData, CadDocument
from interchange.Records.RecordConfig import Configuration


# validated ownership must remain explicit while separate geometry and mate projections prepare their native inputs
@DataClass(frozen=True, slots=True)
class AsmRootData:
    GraphValue: AssemblyData
    RootValue: ComponentDef
    ChildValue: ComponentDef
    ChildDocument: CadDocument
    ConfigValue: Configuration
    Occurrences: tuple[ComponentInst, ...]
    FixedIndex: int
    GroupValue: MateGroup
