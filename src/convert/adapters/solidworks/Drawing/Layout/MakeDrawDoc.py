from hashlib import sha256 as HashSource

from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KDrawingFormatId
from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumDocument import Capability, Severity
from interchange.Enums.EnumUnits import UnitSystem
from interchange.Records.RecordDiagnostic import Diagnostic
from interchange.Records.RecordSource import CadSource
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Models.Drawing.DrawingData import DrawingData

# drawing inspection must identify which editable content still needs decoding
KLayoutDiagnostic = Diagnostic(
    code="slddrw.layout_inspection",
    message=(
        "Decoded sheet layout, model reference, and Definition view placement. "
        "Annotations, native styles, and displayed geometry "
        "are outside this inspection profile."
    ),
    severity=Severity.KWarning,
)


# the public drawing document owns paper layout without fabricating design history
def MakeDrawDoc(
    Archive: SldprtArchive,
    SourceData: bytes,
    Label: str,
    Version: int,
    Drawing: DrawingData,
) -> CadDocument:
    return CadDocument(
        source=CadSource(
            format_id=KDrawingFormatId,
            path=Label,
            sha256=HashSource(SourceData).hexdigest(),
            container_version=str(Archive.format_version),
            attributes=FreezeMapping({"model_archive_version": Version}),
        ),
        configurations=(),
        parameters=(),
        support_planes=(),
        sketches=(),
        selections=(),
        feature_timeline=(),
        bodies=(),
        DrawingValue=Drawing,
        units=UnitSystem.KMeter,
        capabilities=(
            frozenset({Capability.KExternalRefs}) if Drawing.ModelRefs else frozenset()
        ),
        diagnostics=(KLayoutDiagnostic,),
    )
