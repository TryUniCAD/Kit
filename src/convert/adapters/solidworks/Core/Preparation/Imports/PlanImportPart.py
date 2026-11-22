from convert.adapters.solidworks.Archive.Construction.Part.Imports.ReadBareConfig import (
    ReadBareConfig,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.MakeLocalPrism import (
    MakeLocalPrism,
)
from convert.adapters.solidworks.Core.Preparation.Imports.BoxImportPlan import (
    BoxImportPlan,
)
from convert.adapters.solidworks.Core.Preparation.Imports.CheckAxisPlanes import (
    CheckAxisPlanes,
)
from convert.adapters.solidworks.Core.Preparation.Imports.CheckLPrism import (
    CheckLPrism,
)
from convert.adapters.solidworks.Core.Preparation.Imports.HasBoxCorners import (
    HasBoxCorners,
)
from convert.adapters.solidworks.Core.Preparation.Imports.ReadBareModel import (
    ReadBareModel,
)
from interchange.document.Models.DocumentModel import CadDocument


# the fallback checks every retained neutral owner before allocating any native feature
def PlanImportPart(DocumentValue: CadDocument, NameValue: str) -> BoxImportPlan:
    ModelValue = ReadBareModel(DocumentValue)
    ConfigValue = ReadBareConfig(DocumentValue)
    SourceValue = DocumentValue.source
    if any(
        (
            SourceValue.path,
            SourceValue.sha256,
            SourceValue.container_version,
            SourceValue.application_version,
        )
    ):
        raise ValueError("local solid import cannot retain source file identity")
    if any(
        type(LabelValue) is not str
        or not LabelValue.strip()
        or not LabelValue.isprintable()
        for LabelValue in (NameValue, ConfigValue.name)
    ):
        raise ValueError("local solid import requires printable names")
    OwnedBody = not HasBoxCorners(ModelValue)
    if OwnedBody and (
        len(ModelValue.faces),
        len(ModelValue.edges),
        len(ModelValue.vertices),
    ) != (8, 18, 12):
        raise ValueError(
            "local solid import requires one rectangular or L shaped prism"
        )
    NodesValue = MakeLocalPrism(ModelValue)
    CheckAxisPlanes(ModelValue)
    if OwnedBody:
        CheckLPrism(ModelValue)
    return BoxImportPlan(NameValue, ConfigValue.name, NodesValue, OwnedBody=OwnedBody)
