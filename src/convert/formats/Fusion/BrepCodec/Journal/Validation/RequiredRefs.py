KRequiredRefs: dict[str, tuple[int, ...]] = {
    "body": (3,),
    "lump": (4, 5),
    "shell": (5, 7),
    "face": (4, 5, 7),
    "loop": (4, 5),
    "coedge": (3, 4, 5, 6, 8),
    "edge": (3, 5, 7, 8),
    "vertex": (3, 5),
    "ATTRIB_CUSTOM-attrib": (4,),
}
