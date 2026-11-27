from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.ResolvedSchemas import (
    KResolvedSchemas,
)

# mate streams admit only the reached current descriptors at their measured schema revisions
KMatesSchemas = MappingProxyType(
    {
        **KResolvedSchemas,
        "moAbsoluteRefPlnData_c": (1,),
        "moMateCoincident": (1,),
        "moMateParallel": (1,),
        "moMatePerpendicular": (1,),
        "moMateConcentric": (1,),
        "moMateDistanceDim_c": (1,),
        "moPlaneRef_w": (1,),
        "moCylinderRef_w": (1,),
        "moCompRefCylinder_c": (1,),
        "moCompFace_c": (1,),
        "moFacetedData_c": (1,),
        "moRefCylinder_c": (1,),
        "moChainComponent_c": (1,),
        "moExtFeatureList_c": (1,),
        "moReferenceChain_c": (1,),
    }
)
