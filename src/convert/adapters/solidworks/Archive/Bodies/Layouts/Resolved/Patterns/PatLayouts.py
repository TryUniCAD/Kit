from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Patterns.AnglePlaneFields import (
    KAnglePlaneFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Patterns.AxisFields import (
    KAxisFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Patterns.PatRefFields import (
    KPatRefFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Patterns.PatStockFields import (
    KPatStockFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Patterns.PatternDimFields import (
    KPatternDimFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Patterns.PatternLayouts import (
    KPatternFields,
)

# the exact linked ordinary pattern adds only its measured datum stock and display owners
KPatFields = MappingProxyType(
    {
        **KAnglePlaneFields,
        **KAxisFields,
        **KPatRefFields,
        **KPatStockFields,
        **KPatternDimFields,
        **KPatternFields,
    }
)

# every added concrete class uses its actually reached native schema
KPatSchemas = MappingProxyType(
    {
        "moCompRefAxis_c": (1,),
        "moCompSolidBody_c": (1,),
        "moConstraintCoincLineAtAnglePlaneRefplaneData_c": (1,),
        "moConstraintRefplaneInterfaceData_c": (1,),
        "moDisplayDim_c": (1,),
        "moICE_c": (1,),
        "moIntegerParameter_c": (1,),
        "moLPattern_c": (1,),
        "moLineRef_w": (1,),
        "moNumberDim_c": (1,),
        "moPlaneInterAxisData_c": (1,),
        "moPlaneRef_w": (1,),
        "moRefAxis_c": (1,),
        "moRefPlaneAngleGeom_c": (1,),
        "moRefPlaneCoincidentGeom_c": (1,),
    }
)

# pattern roots and displays require only their verified inherited virtual methods
KPatVirtuals = MappingProxyType(
    {
        ("moICE_c", 1000): "moFeature_c.SerializeXmlData",
        ("moIntegerParameter_c", 1000): None,
        ("moLPattern_c", 1000): "moFeature_c.SerializeXmlData",
        ("moRefAxis_c", 1000): "moFeature_c.SerializeXmlData",
        ("moICE_c", 1016): True,
        ("moIntegerParameter_c", 1016): True,
        ("moLPattern_c", 1016): True,
        ("moRefAxis_c", 1016): True,
        ("moICE_c", 1208): "moConcept_c.SerializeLWData",
        ("moIntegerParameter_c", 1208): "moNode_c.SerializeLWData",
        ("moLPattern_c", 1208): "moConcept_c.SerializeLWData",
        ("moRefAxis_c", 1208): "moConcept_c.SerializeLWData",
        ("moICE_c", 1216): "moConcept_c.SerializeResolvedData",
        ("moIntegerParameter_c", 1216): None,
        ("moLPattern_c", 1216): "moConcept_c.SerializeResolvedData",
        ("moRefAxis_c", 1216): "moConcept_c.SerializeResolvedData",
        ("moDisplayDim_c", 2216): 0,
        ("moDisplayDim_c", 2264): 0,
        ("moDisplayDim_c", 2680): 0,
    }
)
