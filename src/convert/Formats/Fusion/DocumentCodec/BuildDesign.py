from convert.Formats.Fusion.DocumentCodec.Model.DesignResult import DesignResult
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.Formats.Fusion.DocumentCodec.Records.EmitDesign import EmitDesign


# the design operation needs a consistent construction rule so model state retains its native feature and ownership relationships
def BuildDesign(SpecValue: DocumentSpec, AssetId: str) -> DesignResult:
    from convert.Formats.Fusion.DocumentCodec.DraftDesign import DraftDesign

    return EmitDesign(DraftDesign(SpecValue, AssetId))
