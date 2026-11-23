from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Core.Preparation.Materials.BuildMatShape import (
    BuildMatShape,
)
from convert.adapters.solidworks.Core.Preparation.Materials.ColdMatSource import (
    KColdMatSource,
    IsColdMatSource,
)
from convert.adapters.solidworks.Core.Preparation.Materials.MatSketchModel import (
    StripMatSketch,
)
from convert.adapters.solidworks.Core.Preparation.RequirePartPath import RequirePartPath
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumDocument import Capability
from interchange.Records.RecordTopology import TopologyCounts


# cold readback state can be removed from the writer input only when it matches its own reconstruction
def MatReadInput(DocumentValue: CadDocument, KindValue: object) -> CadDocument:
    Source = DocumentValue.source
    if not IsColdMatSource(Source):
        return DocumentValue
    Values = Source.attributes
    PathValue, EpochValue = Values.get("native_locator"), Values.get("written_at")
    if (
        not isinstance(KindValue, str)
        or set(Values) != {KColdMatSource, "native_locator", "written_at"}
        or type(PathValue) is not str
        or type(EpochValue) is not int
    ):
        raise ValueError("cold material source lacks its exact archive provenance")
    _ = RequirePartPath(PathValue, EpochValue)
    (SketchValue,) = DocumentValue.sketches
    (BodyValue,) = DocumentValue.bodies
    InputValue = ReplaceValue(
        DocumentValue,
        source=ReplaceValue(Source, attributes={}),
        sketches=(StripMatSketch(SketchValue, KindValue),),
        bodies=(ReplaceValue(BodyValue, topology=TopologyCounts()),),
        brep=None,
        capabilities=DocumentValue.capabilities - {Capability.KBrep},
    )
    if DocumentValue.brep is None:
        if BodyValue.topology != TopologyCounts():
            raise ValueError(
                "cold material design has an unrepresented topology summary"
            )
    else:
        Geometry, Topology = BuildMatShape(InputValue)
        if DocumentValue.brep != Geometry or BodyValue.topology != Topology:
            raise ValueError(
                "cold material geometry disagrees with the actual editable model"
            )
    return InputValue
