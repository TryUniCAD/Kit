from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode


# the closed model supplies actual kernel nodes without carrying any source archive
@DataClass(frozen=True, slots=True)
class BoxImportPlan:
    NameValue: str
    ConfigName: str
    NodesValue: tuple[XmtNode, ...]
    FeatureName: str = "Imported geometry"
    PlaneName: str = "Front Plane"
    SketchName: str = ""
