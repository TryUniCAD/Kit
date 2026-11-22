from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckPointDist import (
    CheckPointDist,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.LineDriver import (
    LineDriver,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimHandle import (
    ReadDimHandle,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadDimView import (
    ReadDimView,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeName import ReadNativeName
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# actual value group objects own named live lengths rather than keyword values or nearby dimension strings
def ReadLineDriver(
    RowValue: Mapping[str, object],
    IndexValue: int,
    DisplayValue: ArchiveNode,
    SketchValue: ArchiveNode,
    LinkValue: NativeLink,
) -> LineDriver:
    NodeValue = RequireNative(RowValue.get("d"), "sgPntPntDist")
    CheckPointDist(NodeValue.FieldsValue)
    Parameter = RequireNative(NodeValue.FieldsValue.get("f28"), "moLengthParameter_c")
    MetresValue = RequireScalar(Parameter.FieldsValue.get("f58"))
    if (
        MetresValue <= 0.0
        or Parameter.FieldsValue.get("f68") != 0
        or Parameter.FieldsValue.get("f48") is not None
    ):
        raise ValueError("typed rectangle length has an alternative parameter value")
    return LineDriver(
        IndexValue,
        NodeValue,
        Parameter,
        ReadDimView(DisplayValue, SketchValue, IndexValue),
        DisplayValue,
        (
            ReadDimHandle(NodeValue.FieldsValue.get("h1"), "sgPointHandle"),
            ReadDimHandle(NodeValue.FieldsValue.get("h2"), "sgPointHandle"),
        ),
        ReadNativeName(Parameter),
        MetresValue,
        NativeNodeSpan(LinkValue, NodeValue),
        NativeNodeSpan(LinkValue, Parameter),
    )
