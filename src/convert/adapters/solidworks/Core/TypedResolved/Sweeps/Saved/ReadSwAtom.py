from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadBodyScalar import (
    ReadBodyScalar,
)
from convert.adapters.solidworks.Core.TypedResolved.BodyNames.ReadOutputAtom import (
    ReadOutputAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.Saved.SwMapClass import (
    SwMapClass,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.SwReadGraph import (
    SwReadGraph,
)
from convert.adapters.solidworks.Core.TypedResolved.Sweeps.ReadSwRow import ReadSwRow


# the actual live atom must be the same member of both configuration and creator arrays
def ReadSwAtom(
    GraphValue: SwReadGraph,
    NodesValue: Mapping[int, XmtNode],
    Attributes: Mapping[str, XmtNode],
) -> ArchiveNode:
    LinkValue, SweepValue = GraphValue.LinkValue, GraphValue.FeatureValue
    AtomValue = ReadOutputAtom(SweepValue)
    Manager = NativeRecord(LinkValue.ConfigValue.RootValue.FieldsValue.get("fd88"))
    SweepFields = SweepValue.FieldsValue
    FeatureId = NativeNodeId(SweepValue)
    BodyId = ReadBodyScalar(NodesValue, Attributes, "ATOM_ID_2001", 1)
    MatchId = ReadBodyScalar(NodesValue, Attributes, "BODY_MATCH", 0)
    if (
        ReadSwRow(Manager, "n6c", "atoms") is not AtomValue
        or SwMapClass(LinkValue.ResolvedValue.MapValue, "moAtom_c") != (AtomValue,)
        or BodyId <= 0
        or MatchId <= 0
        or ReadBodyScalar(NodesValue, Attributes, "LAST_BODY_MODIFYING_FEATURE_ID", 1)
        != FeatureId
        or any(
            AtomValue.FieldsValue.get(KeyValue) != Wanted
            for KeyValue, Wanted in (
                ("f140", BodyId),
                ("f180", MatchId),
                ("f1b0", MatchId),
                ("f12c", FeatureId),
                ("f130", FeatureId),
                ("body_kind", 0),
            )
        )
        or SweepFields.get("f498") != [{"v": BodyId}]
        or SweepFields.get("has_f548") != 0
        or SweepFields.get("f544") != 1
    ):
        raise ValueError(
            "SOLIDWORKS saved sweep solid has a foreign active atom or creator"
        )
    CheckSwMgrLink(GraphValue, BodyId, FeatureId)
    return AtomValue


# the independent manager must link the same result atom and current creator context
def CheckSwMgrLink(GraphValue: SwReadGraph, BodyId: int, FeatureId: int) -> None:
    Manager = GraphValue.LinkValue.ManagerValue
    if Manager is None:
        raise ValueError("SOLIDWORKS saved sweep has no actual configuration manager")
    (LinkedValue,) = SwMapClass(Manager.MapValue, "moLinkedAtomIdNode_c")
    FieldsValue = LinkedValue.FieldsValue
    SweepFields = GraphValue.FeatureValue.FieldsValue
    FirstWord, LastWord = SweepFields.get("f2a4"), SweepFields.get("f2a0")
    if (
        FieldsValue.get("f08") != BodyId
        or FieldsValue.get("f90") != {"n": 1, "items": [{"v": FeatureId}]}
        or FieldsValue.get("fd0") != {"n": 0, "items": []}
        or any(
            FieldsValue.get(KeyValue) for KeyValue in ("ff0", "f100", "f110", "f120")
        )
        or type(FirstWord) is not int
        or type(LastWord) is not int
        or Manager.RootValue.FieldsValue.get("f5b8")
        != [{"a": FeatureId, "b": FirstWord & 0xFFFFFFFF, "c": LastWord & 0xFFFFFFFF}]
    ):
        raise ValueError("SOLIDWORKS saved sweep manager has a foreign result link")
