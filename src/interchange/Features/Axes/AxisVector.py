from typing import TypeAlias

# spatial axis calculations share a fixed length representation for scalar operations
KAxisTriple: TypeAlias = tuple[float, float, float]


# direction and incidence checks need the same oriented spatial product
def CrossAxis(First: KAxisTriple, Second: KAxisTriple) -> KAxisTriple:
    FirstX, FirstY, FirstZ = First
    SecondX, SecondY, SecondZ = Second
    return (
        FirstY * SecondZ - FirstZ * SecondY,
        FirstZ * SecondX - FirstX * SecondZ,
        FirstX * SecondY - FirstY * SecondX,
    )
