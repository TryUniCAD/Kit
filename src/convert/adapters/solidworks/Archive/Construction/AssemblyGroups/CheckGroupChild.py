from ntpath import normcase as NormCase, normpath as NormPath
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import (
    AssemblyInput,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Bounds.MakeChildBox import (
    MakeChildBox,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.CheckAsmChild import (
    CheckAsmChild,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireRecord,
)


# the shared child must remain an actual fully generated ordinary part with its independently selected configuration and a distinct nonvirtual file identity
def CheckGroupChild(ChildValue: PartCandidate, InputValue: AssemblyInput) -> None:
    if type(ChildValue) is not PartCandidate:
        raise TypeError(
            "complete planar groups require the actual generated part candidate"
        )
    CheckAsmChild(ChildValue)
    _ = MakeChildBox(ChildValue)
    if (
        ChildValue.CurrentConfig.FieldsValue.get("owner")
        is not ChildValue.SystemValue.RootValue
        or ChildValue.SystemValue.ManagerValue.FieldsValue["f360"]
        is not ChildValue.CurrentConfig
    ):
        raise ValueError(
            "planar group child lost its actual selected configuration owner"
        )
    FileValue = ArchiveNode.RequireNode(ChildValue.HeaderValue.FieldsValue["f38"])
    FileKey = ReadFileKey(FileValue)
    if (
        FileKey[2] != 2
        or NormCase(NormPath(FileKey[1]))
        == NormCase(NormPath(InputValue.OutputValue.PathName))
        or FieldInt(RequireRecord(FileValue.FieldsValue["shared"]), "f08") != 0
    ):
        raise ValueError(
            "planar group child requires its distinct ordinary external part file"
        )
