from dataclasses import dataclass as DataClass


# native publication needs a complete preflighted archive before opening the destination
@DataClass(frozen=True, slots=True)
class PatCandidate:
    BytesValue: bytes
