from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CheckPartLinks import (
    CheckPartLinks,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadPrincAxis import (
    ReadPrincAxis,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.CheckRevRules import (
    CheckRevRules,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ReadRevFeature import (
    ReadRevFeature,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ReadRevSelect import (
    ReadRevSelect,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ReadRevSense import (
    IsRevReverse,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.ReadRevShape import (
    ReadRevShape,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RequireRevDoc import (
    RequireRevDoc,
)
from convert.adapters.solidworks.Archive.Construction.Revolves.Neutral.RevolvePlan import (
    RevolvePlan,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from interchange.document.Models.DocumentModel import CadDocument


# the constructor needs one complete neutral ownership plan before any archive object or native identifier exists
def ProjectRevolve(DocumentValue: CadDocument) -> RevolvePlan:
    RequireRevDoc(DocumentValue)
    PlaneValue = CheckPartLinks(DocumentValue)
    if ReadPrincAxis(PlaneValue.transform) != "z":
        raise ValueError(
            "ordinary revolve construction requires canonical Front support"
        )
    Definition, AngleValue = ReadRevFeature(DocumentValue)
    SketchValue = DocumentValue.sketches[0]
    AxisEntityId = ReadRevSelect(DocumentValue, Definition)
    ShapeValue = ReadRevShape(SketchValue, AxisEntityId)
    CheckRevRules(SketchValue)
    return RevolvePlan(
        ReadStyleText(DocumentValue.metadata["name"], "neutral document name"),
        DocumentValue.configurations[0].name,
        PlaneValue.name,
        SketchValue.name,
        DocumentValue.feature_timeline[0].name,
        ShapeValue.VerticesValue,
        ShapeValue.AxisStart,
        ShapeValue.AxisEnd,
        AngleValue,
        IsRevReverse(Definition, ShapeValue),
        SketchValue.id,
        DocumentValue.feature_timeline[0].id,
        DocumentValue.parameters[0].id,
        DocumentValue.bodies[0].id,
        DocumentValue.selections[0].id,
        ShapeValue.AxisEntityId,
    )
