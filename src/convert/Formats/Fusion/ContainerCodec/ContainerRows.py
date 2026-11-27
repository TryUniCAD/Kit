from convert.Formats.Fusion.AssetCodec.Zip.ZipAssetRow import ZipAssetRow
from convert.Formats.Fusion.ContainerCodec.CollectRows import CollectRows
from convert.Formats.Fusion.ContainerCodec.Model.FusionContainer import FusionContainer


# container emission needs validated archive members without retaining segment indexes
def ContainerRows(Value: FusionContainer) -> tuple[ZipAssetRow, ...]:
    Entries, _ = CollectRows(Value, KeepIndexes=False)
    return Entries
