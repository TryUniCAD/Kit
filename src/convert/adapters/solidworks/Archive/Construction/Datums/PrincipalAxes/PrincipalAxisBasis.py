from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    KDatumVector,
)

# these are the signed directions of the admitted source model roles in their order
KAxisBasis: tuple[KDatumVector, ...] = (
    (1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
    (0.0, 0.0, 1.0),
)

# the positive intersection selects actual ordered normal pairs on the common origin
KAxisSupports = (("y", "z"), ("z", "x"), ("x", "y"))
