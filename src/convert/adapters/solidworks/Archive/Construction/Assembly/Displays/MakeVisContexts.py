from types import MappingProxyType

from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.MakeExtFeature import (
    MakeExtFeature,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.MakeFileHandle import (
    MakeFileHandle,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.Occurrences.MakeRefChain import (
    MakeRefChain,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue
from convert.adapters.solidworks.Assembly.PlanarMates.ChildSelection import ReadFileText
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
    ReadRows,
    RequireNode,
    RequireRecord,
)

# detached visual file contexts use the measured fresh flag zero reference frame
KContextWords = MappingProxyType(
    {"f48": 0, "f4c": 1, "f50": 0, "f54": 0, "f58": 0, "f60": 0, "f70": 0, "f78": -1}
)

# visual references cannot select a historical or unrelated configuration through their detached chain
KVisUnselected = MappingProxyType({"f08": "", "f10": -1})


# visual context aliases must join the actual generated configuration references before publishing independent detached rows
def MakeVisContexts(
    Config: ArchiveNode,
    HeaderFile: ArchiveNode,
    References: tuple[ArchiveNode, ...],
) -> tuple[tuple[int, ArchiveNode], ...]:
    Shared = RequireRecord(HeaderFile.FieldsValue["shared"])
    Pooled = {
        **Shared,
        **{
            FieldName: MakeFileHandle(ReadFileText(Shared[FieldName]))
            for FieldName in ("h18", "h10")
        },
    }
    for FieldName in ("f38", "f40", "f50"):
        Value = Shared[FieldName]
        if type(Value) is not CStringValue or not Value.IsUnicode or Value.TextValue:
            raise ValueError(
                "assembly visual self-file requires its empty Unicode extensions"
            )
    OwnConfig = {
        "f08": ReadNodeName(Config),
        "f10": FieldInt(Config.FieldsValue, "f08"),
    }
    States = tuple(
        RequireNode(RowValue["o"], "moConfigObject_c")
        for RowValue in ReadRows(Config.FieldsValue["fce8"])
    )
    if len(States) != 3 or States[0].FieldsValue["f10"] is not None:
        raise ValueError(
            "assembly visual context requires both actual configuration member rows"
        )
    Result = []
    for State, Reference in zip(States[1:], reversed(References), strict=True):
        RefFields = Reference.FieldsValue
        FeatureId = FieldInt(RefFields, "f08")
        Context = RequireNode(
            State.FieldsValue["f10"], "moContextChainComponent_c"
        ).FieldsValue
        Chain = RequireNode(Context["f20"], "moReferenceChain_c").FieldsValue
        Targets = RequireNode(Chain["f08"], "moExtFeatureList_c").FieldsValue
        (Target,) = ReadRows(Targets["f08"])
        External = RequireNode(Target["o"], "moExtFeature_c").FieldsValue
        Backlink = RequireNode(RefFields["f4f8"], "moExtFeature_c").FieldsValue
        ContextFile = RequireNode(Context["f40"], "moExtObject_c").FieldsValue
        Stamp = (101 + FieldInt(RefFields, "f3f0")) & 0xFFFFFFFF
        if (
            Context["owner"] is not None
            or Context["f30"] != Stamp
            or Context["f48"] != 0
            or ContextFile != {**KContextWords, "shared": Shared, "refcfg": OwnConfig}
            or ContextFile["shared"] is not Shared
            or External["f10"] is not Shared
            or Backlink["f10"] is not Shared
            or Backlink["f50"] is not Reference
            or Backlink["f44"] != FeatureId
            or State.FieldsValue["f28"] != RefFields["f3c0"]
            or External["f44"] != FeatureId
            or ReadFileText(External["f38"]) != ReadNodeName(Reference)
            or External["f50"] is not None
            or External["f18"] != KVisUnselected
            or External["f40"] != 0
            or External["f58"] != -1
            or Targets["n"] != 1
            or Chain["f24"] != 0
            or Chain["f20"] != 0
            or Chain["f40"] != KVisUnselected
        ):
            raise ValueError(
                "assembly visual context requires the fresh flag-zero links and actual occurrence owners"
            )
        Detached = MakeRefChain(MakeExtFeature(Reference, Pooled, False))
        Detached.FieldsValue["f24"] = 1
        FileNode = ArchiveNode(
            RuntimeClass("moExtObject_c", 1),
            {**KContextWords, "shared": Pooled, "refcfg": dict(KVisUnselected)},
        )
        Result.append(
            (
                FeatureId,
                ArchiveNode(
                    RuntimeClass("moContextChainComponent_c", 1),
                    {
                        "owner": None,
                        "f20": Detached,
                        "f30": Stamp,
                        "f40": FileNode,
                        "f48": 0,
                    },
                ),
            )
        )
    return tuple(Result)
