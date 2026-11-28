from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Displays.AsmDisplayIn import (
    AsmDisplayIn,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Displays.CheckAsmDisplay import (
    CheckAsmDisplay,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Displays.MakeVisContexts import (
    MakeVisContexts,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Displays.MakeVisPlanes import (
    MakeVisPlanes,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.VisualStates.MakeVisKey import MakeVisKey
from convert.adapters.solidworks.Archive.VisualStates.MakeVisRow import MakeVisRow
from convert.adapters.solidworks.Archive.VisualStates.WriteAsmVisual import (
    WriteAsmVisual,
)
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileKey
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    ReadNodeName,
    RequireNode,
)


# selected parent display intent must materialize the binary owner that the native assembly actually applies
def MakeAsmVisual(
    StateValue: AssemblyState,
    ChildValue: PartCandidate,
    HeadersValue: tuple[ArchiveNode, ArchiveNode],
    References: tuple[ArchiveNode, ...],
    MateRoots: tuple[ArchiveNode, ...],
    DisplayValues: tuple[AsmDisplayIn, ...],
) -> bytes:
    Config, States = CheckAsmDisplay(
        StateValue, ChildValue, References, MateRoots, DisplayValues
    )
    Header, TopHeader = (RequireNode(Value, "moHeader_c") for Value in HeadersValue)
    HeaderFields, TopFields = Header.FieldsValue, TopHeader.FieldsValue
    HeaderFile = RequireNode(HeaderFields["f38"], "moExtObject_c")
    NameValue, _, KindValue, _ = ReadFileKey(HeaderFile)
    if (
        Header is TopHeader
        or HeaderFields["fec"] != 1
        or TopFields["fec"] != 0
        or HeaderFields["f38"] is not TopFields["f38"]
        or HeaderFields["f08"] != TopFields["f08"]
        or KindValue != 3
        or NameValue != ReadNodeName(StateValue.RootValue)
    ):
        raise ValueError(
            "assembly visibility requires both actual headers and their shared assembly self-file"
        )
    Contexts = MakeVisContexts(Config, HeaderFile, References)
    Planes = MakeVisPlanes(StateValue, HeadersValue)
    StateKeys = tuple(range(1, len(States) + 1))
    Default = StateKeys[0]
    Property = ArchiveNode(
        RuntimeClass("visStateVisualPropertiesAttribute_c", 1),
        {"f08": Default, "f10": None},
    )
    Display = ArchiveNode(
        RuntimeClass("visStateDisplayStateAttribute_c", 1),
        {"f08": Default, "f10": "<Default>_Display State 1", "f18": Default},
    )
    Flags = RuntimeClass("visStateVisualStateAttribute_c", 1)
    Visibility = {
        Enabled: ArchiveNode(
            Flags, {"f08": Default, "f10": int(Enabled), "f14": 6, "f18": 0, "f1c": 1}
        )
        for Enabled in (False, True)
    }
    Datum = ArchiveNode(Flags, {"f08": Default, "f10": 0, "f14": 6, "f18": 1, "f1c": 0})
    RootValue = MakeVisKey(
        Config,
        tuple(StateName for StateName, _ in States),
        [
            {
                "comp": NodeValue,
                "attrs": [
                    MakeVisRow(
                        StateKey, Property, Visibility[Vector[FeatureId]], Display
                    )
                    for StateKey, (_, Vector) in zip(StateKeys, States, strict=True)
                ],
            }
            for FeatureId, NodeValue in Contexts
        ],
        [
            {
                "ref": NodeValue,
                "attrs": [
                    MakeVisRow(StateKey, Property, Datum) for StateKey in StateKeys
                ],
            }
            for NodeValue in Planes
        ],
    )
    return WriteAsmVisual(RootValue)
