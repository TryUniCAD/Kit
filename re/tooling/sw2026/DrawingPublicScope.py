from pathlib import Path
from uuid import uuid4

from convert.adapters import AdapterNotFoundError
from convert.adapters.solidworks.Container.Format import KDrawingFormatId, KPartFormatId
from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
from convert.api import write_document
from interchange.Enums.EnumUnits import UnitSystem
from interchange.Records.RecordSource import CadSource
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Models.Drawing.DrawingData import DrawingData
from interchange.document.Validation.CheckDrawing import CheckDrawing


def reject_public_write(document: CadDocument) -> None:
    target = Path.cwd() / ("DrawingScope-" + uuid4().hex) / "Candidate.SLDDRW"
    for route, expected in (
        ("inferred", "no writer supports the destination"),
        ("explicit", f"{KPartFormatId} does not support the destination"),
        ("adapter", f"{KPartFormatId} does not support the destination"),
    ):
        try:
            if route == "adapter":
                SldprtAdapter().write(document, target)
            else:
                write_document(document, target, allow_carrier=False,
                               destination_format=KDrawingFormatId if route == "explicit" else None)
        except AdapterNotFoundError as error:
            if str(error) != expected:
                raise
        except (ValueError, TypeError, KeyError, IndexError) as error:
            raise RuntimeError(f"{route} public writer refused outside profile selection") from error
        else:
            raise RuntimeError(f"{route} public writer unexpectedly accepted an unsupported drawing")
        if target.parent.exists():
            raise RuntimeError(f"{route} public writer staged an unsupported drawing")


def refuse_research_drawing(
    document: CadDocument, *, linked: bool, authored: DrawingData | None = None,
) -> dict[str, bool]:
    layout = document.DrawingValue
    if (
        layout is None
        or document.source.format_id != KDrawingFormatId
        or document.source.attributes.get("model_archive_version") != 19000
        or not any(item.code == "slddrw.layout_inspection" for item in document.diagnostics)
        or bool(layout.ModelRefs) != linked
        or any(sheet.Views for sheet in layout.Sheets) != linked
    ):
        raise RuntimeError("public scope check requires the actual version-19000 inspection document")
    reject_public_write(document)
    if linked:
        linked_layout = layout if authored is None else authored
        if CheckDrawing(linked_layout) or not linked_layout.ModelRefs or not any(sheet.Views for sheet in linked_layout.Sheets):
            raise RuntimeError("linked public scope check requires the actual valid model references and views")
        neutral = CadDocument(
            source=CadSource("neutral", "", document.source.sha256),
            configurations=(), parameters=(), support_planes=(), sketches=(),
            selections=(), feature_timeline=(), bodies=(),
            DrawingValue=linked_layout, units=UnitSystem.KMeter,
        )
        reject_public_write(neutral)
    return {"inspection": True, "linked_layout": linked}
