from dataclasses import dataclass as DataClass


# the frozen evaluator needs the complete generated container and its exact constituent streams
@DataClass(frozen=True, slots=True)
class StockCandidate:
    StreamsValue: dict[str, bytes]
    BytesValue: bytes
