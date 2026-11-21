from hashlib import sha256

from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.solidworks.Container.Format import KDrawingFormatId
from convert.adapters.solidworks.Core.DrawingWriting.Rewrite.NeedDrawPath import (
    NeedDrawPath,
)
from convert.adapters.solidworks.Core.DrawingWriting.Rewrite.ReadBlankInput import (
    ReadBlankInput,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.BlankDrawInput import (
    BlankDrawInput,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.MakeBlankFile import (
    MakeBlankFile,
)
from interchange.Enums.EnumUnits import UnitSystem
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Models.Drawing.DrawingData import DrawingData


# complete native source intent must be accounted for before any preserved profile can enter public rewriting
def NeedRewrite(DocumentValue: CadDocument, TargetValue: KTargetType) -> BlankDrawInput:
    NeedDrawPath(TargetValue)
    if (
        type(DocumentValue.DrawingValue) is not DrawingData
        or DocumentValue.units != UnitSystem.KMeter
        or DocumentValue.schema_version != "1.0"
        or any(
            (
                DocumentValue.assembly,
                DocumentValue.brep,
                DocumentValue.configurations,
                DocumentValue.parameters,
                DocumentValue.support_planes,
                DocumentValue.sketches,
                DocumentValue.selections,
                DocumentValue.feature_timeline,
                DocumentValue.bodies,
                DocumentValue.meshes,
                DocumentValue.brep_payloads,
                DocumentValue.materials,
                DocumentValue.diagnostics,
                DocumentValue.capabilities,
            )
        )
        or DocumentValue.source.format_id != KDrawingFormatId
        or DocumentValue.source.container_version != "4"
        or DocumentValue.source.application_version != ""
    ):
        raise ValueError(
            "native blank rewrite excludes unrepresented portable document owners"
        )
    Attributes = DocumentValue.source.attributes
    if set(Attributes) != {
        "model_archive_version",
        "solidworks.blank.profile",
        "solidworks.blank.native_sheet_id",
        "solidworks.blank.intent",
        "solidworks.blank.style_language_selector_is_representative",
        "solidworks.blank.complete_stream_reconstruction",
        "solidworks.blank.complete_container_reconstruction",
    }:
        raise ValueError("native blank rewrite has unknown or missing source owners")
    if (
        Attributes["solidworks.blank.profile"] != "fresh-v19000-seven-stream-v1"
        or type(Attributes["model_archive_version"]) is not int
        or Attributes["model_archive_version"] != 19000
        or any(
            Attributes[KeyValue] is not True
            for KeyValue in (
                "solidworks.blank.style_language_selector_is_representative",
                "solidworks.blank.complete_stream_reconstruction",
                "solidworks.blank.complete_container_reconstruction",
            )
        )
    ):
        raise ValueError("native blank rewrite source profile is unqualified")
    InputValue = ReadBlankInput(Attributes["solidworks.blank.intent"])
    if (
        set(DocumentValue.metadata) != {"name"}
        or DocumentValue.metadata["name"] != InputValue.OptionsValue.NameValue
    ):
        raise ValueError("native blank rewrite has unrepresented model title metadata")
    Original = MakeBlankFile(InputValue)
    NativeSheet = Original.ModelGraph.SheetValue.SheetValue.FieldsValue["f08"]
    if (
        type(Attributes["solidworks.blank.native_sheet_id"]) is not int
        or Attributes["solidworks.blank.native_sheet_id"] != NativeSheet
        or sha256(Original.BytesValue).hexdigest() != DocumentValue.source.sha256
    ):
        raise ValueError(
            "native blank rewrite metadata does not reconstruct its actual source identity"
        )
    if DocumentValue.DrawingValue != InputValue.DrawingValue:
        raise ValueError(
            "native blank rewrite requires the complete unchanged source layout"
        )
    return InputValue
