from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import (
    MaterialSpec,
)
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel
from convert.formats.Fusion.MaterialCodec.Models.ColorValue import ColorValue
from convert.formats.Fusion.MaterialCodec.Models.UnitValue import UnitValue


def NativeMaterial(ModelValue: DocumentModel) -> MaterialSpec:
    if not ModelValue.Bodies:
        if ModelValue.Materials:
            raise ValueError("Unexpected material in a body-free Fusion profile")
        return MaterialSpec()
    if len(ModelValue.Materials) != 1:
        raise ValueError("Qualified Fusion solids require one material package")
    Assets = ModelValue.Materials[0].Package.Assets
    Properties = {
        Field.FieldName: Field.Value for Asset in Assets for Field in Asset.Properties
    }
    Density = Properties.get("structural_Density")
    Color = Properties.get("metal_f0")
    Names = tuple(
        Field.Value
        for Asset in Assets
        if Asset.SchemaName == "PhysMatSchema"
        for Field in Asset.Properties
        if Field.FieldName == "physmat_Label"
    )
    if not isinstance(Density, UnitValue) or not isinstance(Color, ColorValue):
        raise ValueError("Unsupported Fusion physical material projection")
    if len(Names) != 1 or not isinstance(Names[0], str):
        raise ValueError("Unsupported Fusion material name")
    return MaterialSpec(Names[0], Density.Magnitude, Color)
