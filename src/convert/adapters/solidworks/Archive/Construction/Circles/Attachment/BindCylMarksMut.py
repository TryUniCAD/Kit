from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.CylPartition import (
    CylPartition,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# part activation and feature selection marks bind independently to the same live atom
def BindCylMarksMut(
    ChildValue: PartCandidate,
    AtomValue: ArchiveNode,
    NativeValue: CylPartition,
) -> None:
    RootValue = ChildValue.SystemValue.RootValue
    TagValue = NativeValue.BodyTag
    AtomValue.FieldsValue.update(f180=TagValue, f1b0=TagValue, f188=1)
    RootValue.FieldsValue.update(
        fe38=ArchiveNode(
            RuntimeClass("moPMarkRecord_c", 1), {"f18": NativeValue.ActivationId}
        ),
        f1010=1,
        nff4=1,
        ffe0=[{"k": AtomValue, "v": int(FieldInt(AtomValue.FieldsValue, "f170") != 0)}],
    )
    ChildValue.BossValue.FeatureValue.FieldsValue.update(
        has_f3d0=1,
        f3d0=ArchiveNode(
            RuntimeClass("moPMarkRecord_c", 1), {"f18": NativeValue.SelectedId}
        ),
        f3c0=0,
        f3c8=0,
        f580=0,
        f540=3,
    )
