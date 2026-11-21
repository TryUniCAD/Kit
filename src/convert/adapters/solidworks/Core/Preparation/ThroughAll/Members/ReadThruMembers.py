from convert.adapters.solidworks.Archive.Construction.System.Members.MemberInput import (
    MemberInput,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.MemberPlan import (
    MemberPlan,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.CheckMemberRows import (
    CheckMemberRows,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadLightInput import (
    ReadLightInput,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadNotesInput import (
    ReadNotesInput,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Source.CheckSourceEnv import (
    CheckSourceEnv,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.SourceConfig.CheckThruLink import (
    CheckThruLink,
)
from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadChildren import (
    ReadChildren,
)
from interchange.document.Models.DocumentModel import CadDocument


# source members must be reached through actual cabinet and shared environment ownership rather than nearby names
def ReadThruMembers(DocumentValue: CadDocument, LinkValue: NativeLink) -> MemberPlan:
    CheckSourceEnv(DocumentValue)
    CheckThruLink(DocumentValue, LinkValue)
    Features = tuple(IndexFeatures(LinkValue).values())
    Cabinets = tuple(
        ValueInput
        for ValueInput in Features
        if ValueInput.ClassValue.NameValue == "moDetailCabinet_c"
    )
    Folders = tuple(
        ValueInput
        for ValueInput in Features
        if ValueInput.ClassValue.NameValue == "moEnvFolder_c"
    )
    if (
        len(Cabinets) != 1
        or len(Folders) != 1
        or LinkValue.ConfigValue.RootValue.FieldsValue.get("f1e0") is not Folders[0]
    ):
        raise ValueError(
            "source members lack their actual unique cabinet and environment"
        )
    NotesValue = ReadChildren(Cabinets[0])
    LightsValue = ReadChildren(Folders[0])
    CheckMemberRows(DocumentValue, Cabinets[0], NotesValue)
    CheckMemberRows(DocumentValue, Folders[0], LightsValue)
    InputValue = MemberInput(
        ReadNotesInput(NotesValue),
        tuple(ReadLightInput(ValueInput) for ValueInput in LightsValue),
    )
    if tuple(ValueInput.KindValue for ValueInput in InputValue.LightValues) != (
        "ambient",
        "directional",
        "directional",
        "directional",
    ):
        raise ValueError(
            "source scene is outside the witnessed ordinary through cut profile"
        )
    IdValues = tuple(
        "sldprt:feature:" + str(NativeNodeId(ValueInput))
        for ValueInput in (*NotesValue, *LightsValue)
    )
    if len(set(IdValues)) != len(IdValues):
        raise ValueError("source member identities are ambiguous")
    return MemberPlan(InputValue, (IdValues[0], IdValues[1]), IdValues[2:])
