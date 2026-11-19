from convert.adapters.solidworks.Archive.Construction.System.Members.LightInput import (
    LightInput,
)
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadMemberTime import (
    ReadMemberTime,
)
from convert.adapters.solidworks.Archive.Definition.Construction.RequireDefNumber import (
    RequireDefNumber,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    FieldText,
    ReadNodeName,
    RequireRecord,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# light properties must come from named native semantic owners with unsupported suppression and user data refused
def ReadLightInput(NodeValue: ArchiveNode) -> LightInput:
    ClassName = NodeValue.ClassValue.NameValue
    if ClassName not in ("moAmbientLight_c", "moDirectionLight_c"):
        raise ValueError("source light class is outside the qualified member profile")
    _ = RequireNative(NodeValue, ClassName)
    Values = NodeValue.FieldsValue
    SwitchNames = ("f388", "f384", "f4f0", "f488")
    Switches = tuple(FieldInt(Values, NameValue) for NameValue in SwitchNames)
    if (
        any(ValueInput not in (0, 1) for ValueInput in Switches)
        or FieldInt(Values, "f384#0") != Switches[1]
    ):
        raise ValueError(
            "source light switches differ from their mapped boolean owners"
        )
    if (
        any(
            FieldInt(Values, NameValue) != 0
            for NameValue in ("f35c", "f0c", "state", "f36c")
        )
        or FieldInt(Values, "f428") != 1
        or RequireRecord(Values.get("f500")) != {"n": 0, "props": []}
    ):
        raise ValueError(
            "source light has unsupported status coordinate or user property state"
        )
    Direction = None
    Softness = None
    if ClassName == "moDirectionLight_c":
        VectorValue = RequireRecord(Values.get("f3b0"))
        Direction = (
            RequireDefNumber(VectorValue.get("x")),
            RequireDefNumber(VectorValue.get("y")),
            RequireDefNumber(VectorValue.get("z")),
        )
        Softness = RequireDefNumber(Values.get("f498"))
    return LightInput(
        "ambient" if ClassName == "moAmbientLight_c" else "directional",
        ReadNodeName(NodeValue),
        FieldText(Values, "f4f8"),
        RequireDefNumber(Values.get("f390")),
        RequireDefNumber(Values.get("f398")),
        RequireDefNumber(Values.get("f3a0")),
        FieldInt(Values, "f3a8"),
        bool(Switches[0]),
        bool(Switches[1]),
        bool(Switches[2]),
        RequireDefNumber(Values.get("f478")),
        bool(Switches[3]),
        RequireDefNumber(Values.get("f490")),
        Direction,
        Softness,
        ReadMemberTime(NodeValue),
    )
