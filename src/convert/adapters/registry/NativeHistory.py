from convert.adapters.base.ContractTypes import KTargetType
from convert.adapters.base.DepthlessWriter import DepthlessWriter
from convert.adapters.registry.NativeEnds import EndFindings
from convert.adapters.registry.NativeAssembly import AssemblyIssues
from convert.adapters.registry.NativeFeatures import FeatureFindings
from convert.adapters.registry.NativeSketch import SketchFindings
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Models.DocumentWalk import WalkDocuments
from interchange.Features.FeatureKinds import NativeFeature


# shared conversion boundaries must reject incomplete native history even after source relabeling
def CheckHistory(
    Document: CadDocument,
    WriterValue: object = None,
    TargetValue: KTargetType | None = None,
) -> None:
    Findings = sorted(
        {
            f"{PartValue.source.path}: {StepValue.id} ({Definition.format_id}:{Definition.type_id})"
            for PartValue in WalkDocuments(Document)
            for StepValue in PartValue.feature_timeline
            for Definition in (StepValue.definition,)
            if isinstance(Definition, NativeFeature)
        }
    )
    if Findings:
        raise ValueError(
            "native-only feature definitions cannot be exported: " + "; ".join(Findings)
        )
    ThroughEndId = (
        WriterValue.ProveThroughEnd(Document, TargetValue)
        if TargetValue is not None and isinstance(WriterValue, DepthlessWriter)
        else None
    )
    Findings = sorted(
        {
            Finding
            for PartValue in WalkDocuments(Document)
            for Finding in (
                *SketchFindings(PartValue),
                *EndFindings(
                    PartValue, ThroughEndId if PartValue is Document else None
                ),
                *FeatureFindings(PartValue),
                *AssemblyIssues(PartValue),
            )
        }
    )
    if Findings:
        raise ValueError(
            "native or unresolved required semantics cannot be exported: "
            + "; ".join(Findings)
        )
