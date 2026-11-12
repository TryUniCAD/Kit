from datetime import UTC, datetime as DateTime

from convert.formats.Fusion.DocumentCodec.Materials.CheckMaterial import CheckMaterial
from convert.formats.Fusion.DocumentCodec.Materials.CreateMatIds import CreateMatIds
from convert.formats.Fusion.DocumentCodec.Materials.MaterialAssets import MaterialAssets
from convert.formats.Fusion.DocumentCodec.Materials.Model.AuthoredMat import AuthoredMat
from convert.formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec import (
    MaterialSpec,
)
from convert.formats.Fusion.DocumentCodec.Materials.Vocabulary.ReadMatSchema import (
    ReadMatSchema,
)
from convert.formats.Fusion.MaterialCodec.Package.MakePackage import MakePackage


def BuildMaterial(SpecValue: MaterialSpec) -> AuthoredMat:
    CheckMaterial(SpecValue)
    Identity = CreateMatIds()
    Schemas = ReadMatSchema()
    Assets = MaterialAssets(SpecValue, Identity, Schemas)
    Package = MakePackage(
        Identity.PackageId,
        Identity.AssetId,
        DateTime.now(UTC).isoformat(),
        Schemas,
        Assets,
    )
    return AuthoredMat(Identity, Package)
