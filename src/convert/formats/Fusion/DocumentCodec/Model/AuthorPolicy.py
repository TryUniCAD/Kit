from dataclasses import dataclass as MakeDataClass


@MakeDataClass(frozen=True, slots=True)
class AuthorPolicy:
    FirstDesignId: int = 1000
    DesignSegmentId: int = 0
    ActSegmentId: int = 1
    ParamBirthday: int = 6
    TimeStamp: int = 0
    SketchGeneration: int = 2
    FirstSketchTag: int = 100
    FirstOperationId: int = 300
    BodyKey: int = 0
    GenerationRef: int = 4
    HistoryCurrentId: int = 4
    HistoryInitialId: int = 2
    HistoryGeneration: int = 4
    HistoryAllocation: int = 1
    HistoryBoardNumber: int = 2
    SideFaceLabel: str = "3"
    TopFaceLabel: str = "2"
    BottomFaceLabel: str = "1"
    TopEdgeLabel: str = "-1"
    BodyOccurrenceCount: int = 1
    CurveProgenitorTag: int = 3
    BodyProgenitorTag: int = 4
