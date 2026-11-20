from convert.adapters.freecad.Archive import ConstraintsProp, ParamCatalog
from convert.adapters.freecad.EditRead.Sketch.SavedRuleTable import ReadRuleRows
from convert.adapters.freecad.EditRead.Sketch.SavedSketchRules import CheckStaticRow
from interchange.serialization.EncodeData import ToData
from convert.adapters.freecad.EditRead.EditGeometry import CheckEditGeom
from convert.adapters.freecad.EditRead.XmlField import EditChild
from convert.adapters.freecad.Native import NativeObject
from interchange.geometry.Models.Sketch import Sketch


# geometry and solver lists must still describe the exact selected circle
def CheckEditSketch(Native: NativeObject, Original: Sketch) -> None:
    Geometries = EditChild(
        Native, "Geometry", "Part::PropertyGeometryList", "GeometryList"
    )
    if Geometries.get("count") != str(len(Original.entities)) or len(Geometries) != len(
        Original.entities
    ):
        raise ValueError("FreeCAD editable sketch geometry count changed")
    Selected = Original.closed_profile_entity_ids[0][0]
    for Index, (NodeValue, Entity) in enumerate(zip(Geometries, Original.entities), 1):
        if NodeValue.tag != "Geometry" or NodeValue.get("id") != str(Index):
            raise ValueError("FreeCAD editable sketch geometry order changed")
        CheckEditGeom(NodeValue, Entity, Entity.id == Selected)
    SketchData = ToData(Original)
    if not isinstance(SketchData, dict):
        raise ValueError("FreeCAD editable sketch source is invalid")
    Indices = {Entity.id: Index for Index, Entity in enumerate(Original.entities)}
    Template, Expressions, Dependencies, Diagnostics = ConstraintsProp(
        SketchData, Indices, ParamCatalog([])
    )
    if (
        Expressions
        or Dependencies
        or Diagnostics
        or len(Template) != 1
        or len(Template[0]) != sum(Entity.fixed for Entity in Original.entities)
    ):
        raise ValueError("FreeCAD editable sketch constraints changed")
    for RowValue in ReadRuleRows(Native, Template):
        CheckStaticRow(RowValue)
    if "ExternalGeometry" in Native.properties:
        External = EditChild(
            Native, "ExternalGeometry", "App::PropertyLinkSubList", "LinkSubList"
        )
        if len(External) or External.get("count") != "0":
            raise ValueError("FreeCAD editable sketch external references changed")
