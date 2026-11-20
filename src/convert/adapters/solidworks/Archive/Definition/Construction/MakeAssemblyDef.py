from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Definition.Construction.MakeDefHead import (
    MakeDefHead,
)
from convert.adapters.solidworks.Archive.Definition.Construction.MakeDefTail import (
    MakeDefTail,
)
from convert.adapters.solidworks.Archive.Definition.Construction.MakeSavePartSettings import (
    MakeSavePrefs,
)
from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import (
    ModelDefInput,
)
from convert.adapters.solidworks.Archive.Definition.ModelDefGraph import ModelDefGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# fresh assemblies build their own inline options after the shared document state
def MakeAssemblyDef(
    Settings: ModelDefInput, PreferenceValues: Mapping[str, bool | int | float]
) -> ModelDefGraph:
    FieldValues = (
        MakeDefHead(Settings)
        | MakeDefTail()
        | {
            "f1840": 0,
            "f19c8": 0,
            "f1a38": "",
            "f1a40": "",
            "f1a48": 0,
            "f19b0": 0,
            "f19b8": 0.0127,
            "f19c0": 0,
            "f1b48": MakeSavePrefs(PreferenceValues),
            "f1afc": 10,
        }
    )
    return ModelDefGraph(
        ArchiveNode(RuntimeClass("uiAssemblyDoc_c", 1), FieldValues),
        Settings.VersionValue,
    )
