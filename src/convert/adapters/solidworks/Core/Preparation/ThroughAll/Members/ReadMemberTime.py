from convert.adapters.solidworks.Archive.Construction.Chronology.FeatureInstant import (
    FeatureInstant,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# source member creation precision must survive without forwarding encoded clock words
def ReadMemberTime(NodeValue: ArchiveNode) -> FeatureInstant:
    LowValue = FieldInt(NodeValue.FieldsValue, "f2a0")
    HighValue = FieldInt(NodeValue.FieldsValue, "f2a4")
    if any(
        not -(1 << 31) <= ValueInput < 1 << 31 for ValueInput in (LowValue, HighValue)
    ):
        raise ValueError("member creation words exceed native signed width")
    TicksValue = ((HighValue & 0xFFFFFFFF) << 32) | (LowValue & 0xFFFFFFFF)
    if not TicksValue:
        raise ValueError("unset member creation is outside this source profile")
    SecondsValue, FractionValue = divmod(TicksValue - 11644473600 * 10000000, 10000000)
    return FeatureInstant(SecondsValue, FractionValue)
