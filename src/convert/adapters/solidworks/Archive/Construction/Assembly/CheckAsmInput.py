from ntpath import (
    normcase as NormCase,
    normpath as NormPath,
)
from typing import cast as CastValue
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyInput import (
    AssemblyInput,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyMateIn import (
    AssemblyMateIn,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.CheckAsmChild import (
    CheckAsmChild,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.CheckAsmNames import (
    CheckAsmNames,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.CheckAsmMeta import (
    CheckAsmMeta,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.OccurrenceIn import (
    OccurrenceIn,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.MakePlacement import (
    MakePlacement,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Xml.ReadOccName import (
    ReadOccName,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.FieldRecord import (
    FieldRecord,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey


# first complete assembly admission requires one actual generated child two distinct rigid occurrences and coherent explicit document provenance
def CheckAsmInput(
    ChildValue: PartCandidate,
    InputValue: AssemblyInput,
    Occurrences: tuple[OccurrenceIn, OccurrenceIn],
    MateValue: AssemblyMateIn,
) -> None:
    if (
        type(ChildValue) is not PartCandidate
        or type(InputValue) is not AssemblyInput
        or type(MateValue) is not AssemblyMateIn
    ):
        raise TypeError(
            "complete assembly requires actual generated child and typed construction inputs"
        )
    if (
        type(Occurrences) is not tuple
        or len(CastValue(tuple[object, ...], Occurrences)) != 2
        or any(type(ItemValue) is not OccurrenceIn for ItemValue in Occurrences)
    ):
        raise ValueError(
            "complete ordinary assembly requires two explicit resolved part occurrences"
        )
    if len({ItemValue.NameValue for ItemValue in Occurrences}) != 2:
        raise ValueError("assembly occurrence names must be distinct")
    CheckAsmChild(ChildValue)
    CheckAsmNames(InputValue, Occurrences, MateValue)
    for ItemValue in Occurrences:
        _ = MakePlacement(ItemValue.FrameValue)
        _ = ReadOccName(ItemValue.NameValue)
    if (
        ChildValue.CurrentConfig.FieldsValue.get("owner")
        is not ChildValue.SystemValue.RootValue
        or ChildValue.SystemValue.ManagerValue.FieldsValue["f360"]
        is not ChildValue.CurrentConfig
    ):
        raise ValueError(
            "generated child has lost its actual independent active configuration"
        )
    ChildFile = ArchiveNode.RequireNode(ChildValue.HeaderValue.FieldsValue["f38"])
    ChildPath = ReadFileKey(ChildFile)[1]
    if ReadFileKey(ChildFile)[2] != 2 or NormCase(NormPath(ChildPath)) == NormCase(
        NormPath(InputValue.OutputValue.PathName)
    ):
        raise ValueError(
            "assembly and generated child must retain different ordinary file identities"
        )
    CheckAsmMeta(InputValue)
    if FieldRecord(ChildFile.FieldsValue["shared"])["f08"] != 0:
        raise ValueError("complete assembly does not admit a virtual child definition")
