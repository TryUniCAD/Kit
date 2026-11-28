from dataclasses import dataclass as DataClass


# source operation and geometry identities must remain inspectable without becoming native allocation numbers
@DataClass(frozen=True, slots=True)
class SourceRefs:
    StockProfileId: str
    CutProfileId: str
    CutFeatureId: str
    CutSketchId: str
    CircleId: str
    CenterId: str
    ScopeId: str
    StockParents: tuple[str, ...]
    CutParents: tuple[str, ...]
    StockOperation: str
