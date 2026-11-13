from dataclasses import dataclass as MakeDataClass
from convert.formats.Fusion.GraphicsCodec.Model.Values.AppliedSet import AppliedSet
from convert.formats.Fusion.GraphicsCodec.Model.Values.NodeTarget import NodeTarget


@MakeDataClass(frozen=True, slots=True)
class OverrideSet:
    SetValue: AppliedSet
    Target: NodeTarget
    ChildSets: tuple[AppliedSet, ...]
