# only these subclasses share the independently witnessed distance layout
KDistanceTypes = ("sgPntPntDist", "sgPntPntHorDist", "sgPntPntVertDist")

# these wrappers carry the local proxy through its typed feature and entity references
KProxyTypes = ("sgExtEnt_c", "moSketchExtRef_w", "moCompSketchEntHandle_c")

# common payload types are explicit so enclosing equation readers can delegate them
KSketchTypes = (
    KDistanceTypes
    + KProxyTypes
    + (
        "sgPointHandle",
        "sgLineHandle",
        "moPointBackedUpData_c",
        "moNodeName_c",
        "moLengthParameter_c",
    )
)
