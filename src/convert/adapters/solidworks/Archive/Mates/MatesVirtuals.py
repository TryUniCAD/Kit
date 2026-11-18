from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.ResolvedVirtuals import (
    KResolvedVirtuals,
)

# concrete planar mates use their bound concept serialization dispatch rather than name heuristics
KMatesVirtuals = MappingProxyType(
    {
        **KResolvedVirtuals,
        ("moMateCoincident", 1000): "moFeature_c.SerializeXmlData",
        ("moMateParallel", 1000): "moFeature_c.SerializeXmlData",
        ("moMatePerpendicular", 1000): "moFeature_c.SerializeXmlData",
        ("moMateDistanceDim_c", 1000): "moFeature_c.SerializeXmlData",
        ("moMateCoincident", 1016): True,
        ("moMateParallel", 1016): True,
        ("moMatePerpendicular", 1016): True,
        ("moMateDistanceDim_c", 1016): True,
        ("moMateCoincident", 1208): "moConcept_c.SerializeLWData",
        ("moMateParallel", 1208): "moConcept_c.SerializeLWData",
        ("moMatePerpendicular", 1208): "moConcept_c.SerializeLWData",
        ("moMateDistanceDim_c", 1208): "moConcept_c.SerializeLWData",
        ("moMateCoincident", 1216): "moConcept_c.SerializeResolvedData",
        ("moMateParallel", 1216): "moConcept_c.SerializeResolvedData",
        ("moMatePerpendicular", 1216): "moConcept_c.SerializeResolvedData",
        ("moMateDistanceDim_c", 1216): "moConcept_c.SerializeResolvedData",
    }
)
