from convert.formats.Fusion.EntityCodec.Model.ValueSeries import ValueSeries
from convert.formats.Fusion.EntityCodec.Model.ValueTypes import KEntityValue
from convert.formats.Fusion.MaterialCodec.Package.Model.MaterialPackage import (
    MaterialPackage,
)


def CheckAssetRefs(
    Fields: dict[str, KEntityValue],
    Package: MaterialPackage,
    Prefix: str,
    RoleName: str,
) -> None:
    References = Fields.get(Prefix + "AssetReferences")
    Counts = Fields.get(Prefix + "RefCountVector")
    if (
        not isinstance(References, ValueSeries)
        or not isinstance(Counts, ValueSeries)
        or len(References.Items) != len(Counts.Items)
    ):
        raise ValueError("Invalid document material manager reference vectors")
    Assets = {Asset.InstanceId: Asset for Asset in Package.Assets}
    for Identity, Count in zip(References.Items, Counts.Items, strict=True):
        if (
            not isinstance(Identity, str)
            or Identity not in Assets
            or Assets[Identity].AssetRole != RoleName
            or type(Count) is not int
            or Count < 0
        ):
            raise ValueError(
                "Document material manager references a missing or incompatible asset"
            )
