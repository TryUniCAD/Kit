from struct import pack as PackValues
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeDimValue import (
    MakeDimValue,
)
from convert.adapters.solidworks.Archive.Construction.Dimensions.MakeHandleMut import (
    MakeHandleMut,
)
from convert.adapters.solidworks.Archive.Construction.Extrusion.MakeExtrusionView import (
    MakeExtrudeView,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.InitNodeMut import (
    InitNodeMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Feature.SetWallFrameMut import (
    SetWallFrameMut,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# the distinct thin parameter and display cache retain the same live authored thickness
def MakeThinDimMut(
    FeatureValue: ArchiveNode,
    InputValue: PartBuildInput,
    Allocator: PersistentIds,
    SupportValue: PlaneFrame,
    NameValue: str,
    LengthValue: float,
    SpanValue: tuple[float, float, float] | None,
) -> ArchiveNode:
    Parameter = ArchiveNode(RuntimeClass("moLengthParameter_c", 1), {})
    InitNodeMut(Parameter, NameValue)
    Parameter.FieldsValue.update(
        owner=FeatureValue, f0c=0, f48=None, f58=LengthValue, f68=0
    )
    Dimension = MakeDimValue(FeatureValue, Parameter)
    _ = Allocator.AllocateMut(Dimension, "f50")
    if SpanValue is not None:
        SetWallFrameMut(Dimension, SupportValue, SpanValue)
    HandleValue = MakeHandleMut(FeatureValue, Dimension)
    DisplayValue = MakeExtrudeView(
        FeatureValue,
        HandleValue,
        False,
        InputValue.DesignIntent,
        InputValue.SelectedLeader,
    )
    CacheValue = CastValue(dict[str, object], DisplayValue.FieldsValue["f5b0"])
    CacheValue["data"] = PackValues("<d", LengthValue)
    return DisplayValue
