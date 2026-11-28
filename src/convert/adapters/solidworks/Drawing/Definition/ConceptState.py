from dataclasses import dataclass as DataClass


# conditions belong to the nested drawing serializers and restore on return
@DataClass(slots=True)
class ConceptState:
    Conditions: int = 0
    CallDepth: int = 0
