from dataclasses import dataclass as DataClass


# the complete batch ties exact generation rows to independently measured native lifecycles
@DataClass(frozen=True, slots=True)
class PairBatch:
    Destination: str
    Generated: tuple[dict[str, object], ...]
    Cases: tuple[dict[str, object], ...]
    PhaseHashes: tuple[tuple[str, str], ...]
    GenerationHash: str
    NativeHash: str
