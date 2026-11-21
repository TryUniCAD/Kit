from convert.adapters.solidworks.Archive.Construction.Files.MakeFileConfig import (
    MakeFileConfig,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.IdentityXform import (
    IdentityXform,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import (
    InitFeatureMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# ordinary drawing references copy only live child update counters and preserve separate actual owning reference and directory identities
def MakeDrawRef(
    ClassName: str,
    NameValue: str,
    OwnerValue: ArchiveNode,
    ChildValue: PartCandidate,
    EntryValue: ArchiveNode,
    TargetValue: FeatureTarget,
    Allocator: PersistentIds | None,
) -> ArchiveNode:
    if ClassName not in ("moReferenceInternal_c", "moReferenceModel_c"):
        raise ValueError(
            "drawing reference construction requires a qualified concrete reference class"
        )
    Result = ArchiveNode(RuntimeClass(ClassName, 1), {})
    InitFeatureMut(Result, NameValue, OwnerValue, TargetValue, Allocator)
    FieldsValue = Result.FieldsValue
    FieldsValue.update(
        dict.fromkeys(
            (
                "has_discarded_xform",
                "has_f378",
                "has_f370",
                "f388",
                "f408",
                "f418",
                "f41c",
                "f450",
                "f454",
                "f458",
                "f49c",
                "f4a0",
                "f4c0",
                "f4d8",
                "f4dc",
                "f4f0",
                "f524",
                "f530",
                "f550",
                "f368",
            ),
            0,
        )
    )
    FieldsValue.update(
        dict.fromkeys(
            ("f468", "f470", "f488", "f490", "f4f8", "f538", "f548", "discarded_stack"),
            None,
        )
    )
    FieldsValue.update(
        {
            "f3e0": FieldInt(ChildValue.HeaderValue.FieldsValue, "f40"),
            "f3e8": FieldInt(ChildValue.HeaderValue.FieldsValue, "f48"),
            "f3f4": FieldInt(ChildValue.SystemValue.RootValue.FieldsValue, "f1300"),
            "f3f0": 102,
            "f3f8": 101,
            "has_f360": 1,
            "f360": IdentityXform(),
            "f3b0": EntryValue,
            "f3c0": MakeFileConfig(
                ChildValue.SystemValue.RootValue, ChildValue.CurrentConfig
            ),
            "f3dc": -1,
            "f400": 3,
            "f4a4": -1,
            "f4b0": -1,
            "f4b4": -1,
            "f500": "",
            "f508": "",
            "f55c": 101,
        }
    )
    return Result
