from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import (
    MaterialSpec,
)
from convert.formats.Fusion.DocumentCodec.Materials.ProjectMaterial import (
    ProjectMaterial,
)
from convert.formats.Fusion.DocumentCodec.Model.DocumentModel import DocumentModel


def NativeMaterial(ModelValue: DocumentModel) -> MaterialSpec:
    if not ModelValue.Bodies:
        if ModelValue.Materials:
            raise ValueError("Unexpected material in a body-free Fusion profile")
        return MaterialSpec()
    if len(ModelValue.Materials) != 1:
        raise ValueError("Qualified Fusion solids require one material package")
    Package = ModelValue.Materials[0].Package
    Physical = tuple(
        Asset.InstanceId
        for Asset in Package.Assets
        if Asset.SchemaName == "PhysMatSchema"
    )
    if len(Physical) != 1:
        raise ValueError("Unsupported Fusion physical material projection")
    return ProjectMaterial(Package, Physical[0])
