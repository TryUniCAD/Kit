from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSingleNode import (
    ReadSingleNode,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# selected body presentation must retain actual wrapper component and chooser objects rather than copied field payloads
def CheckThruScope(LinkValue: NativeLink, CutValue: ExtrudeOwner) -> None:
    FieldsValue = CutValue.NodeValue.FieldsValue
    WrapperValue = ReadSingleNode(FieldsValue.get("f548"), "moCompSolidBody_c")
    ComponentValue = RequireNative(WrapperValue.FieldsValue.get("f58"))
    ChooserValue = NativeRecord(FieldsValue.get("f4c0"))
    DataValue = ReadSingleNode(ChooserValue.get("f48"), "moPerBodyChooserData_c")
    CheckTreeAlias(LinkValue, (WrapperValue, ComponentValue, DataValue))
