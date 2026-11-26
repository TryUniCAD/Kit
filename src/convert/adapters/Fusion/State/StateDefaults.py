from convert.Formats.Fusion.BrepCodec.Prism.Models.PrismIds import PrismIds
from convert.Formats.Fusion.DocumentCodec.Materials.Model.FinishSpec import FinishSpec
from convert.Formats.Fusion.DocumentCodec.Materials.Model.MechanicSpec import (
    MechanicSpec,
)

# legacy field defaults stay declarative while explicit source values retain precedence
KStateDefaults: dict[str, dict[str, object]] = {
    "convert.Formats.Fusion.BrepCodec.Prism.Models.PrismHistory.PrismHistory": {
        "Tracking": PrismIds(),
    },
    "convert.Formats.Fusion.DocumentCodec.Model.DocumentModel.DocumentModel": {
        "Meshes": (),
        "Forms": (),
    },
    "convert.Formats.Fusion.DocumentCodec.Model.ParsedSegment.ParsedSegment": {
        "BulkSlack": b"",
    },
    "convert.Formats.Fusion.GraphicsCodec.Model.Nodes.SketchWorld.SketchWorld": {
        "RegularNodes": (),
        "NoCullingNodes": (),
    },
    "convert.Formats.Fusion.DocumentCodec.Materials.Model.MaterialSpec.MaterialSpec": {
        "ClassName": "Generic",
        "Mechanics": MechanicSpec(),
        "Thermal": None,
        "Finish": FinishSpec(),
        "TypeName": None,
    },
}
