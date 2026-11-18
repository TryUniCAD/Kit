from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.ResolvedSchemas import (
    KResolvedSchemas,
)

# only the reached ordinary planar descriptors gain current schema admission in mate streams
KMatesSchemas = MappingProxyType(
    {
        **KResolvedSchemas,
        "moAbsoluteRefPlnData_c": (1,),
        "moMateCoincident": (1,),
        "moMateParallel": (1,),
        "moMatePerpendicular": (1,),
        "moMateDistanceDim_c": (1,),
        "moPlaneRef_w": (1,),
        "moChainComponent_c": (1,),
        "moExtFeatureList_c": (1,),
        "moReferenceChain_c": (1,),
    }
)
