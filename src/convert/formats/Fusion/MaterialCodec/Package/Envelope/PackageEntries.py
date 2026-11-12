from convert.formats.Fusion.MaterialCodec.Package.Envelope.EmitCore import EmitCore
from convert.formats.Fusion.MaterialCodec.Package.Envelope.EmitLinks import EmitLinks
from convert.formats.Fusion.MaterialCodec.Package.Envelope.EmitResources import (
    EmitResources,
)
from convert.formats.Fusion.MaterialCodec.Package.Envelope.FormatEntries import (
    FormatEntries,
)
from convert.formats.Fusion.MaterialCodec.Package.Model.MaterialPackage import (
    MaterialPackage,
)


def PackageEntries(Value: MaterialPackage) -> dict[str, bytes]:
    Prefix = Value.AssetCore.Identifier + "/"
    Result = FormatEntries()
    Result.update(
        {
            "cnx.xml": EmitLinks((Value.AssetCore.Identifier,)),
            "core.xml": EmitCore(Value.RootCore),
            Prefix + "cnx.xml": EmitLinks(("AssetData", "Schemas")),
            Prefix + "core.xml": EmitCore(Value.AssetCore),
            Prefix + "AssetData/core.xml": EmitCore(Value.DataCore),
            Prefix + "Schemas/core.xml": EmitCore(Value.SchemaCore),
            Prefix + "AssetData/cnx.xml": EmitResources(Value.DataLinks),
            Prefix + "Schemas/cnx.xml": EmitResources(Value.SchemaLinks),
        }
    )
    return Result
