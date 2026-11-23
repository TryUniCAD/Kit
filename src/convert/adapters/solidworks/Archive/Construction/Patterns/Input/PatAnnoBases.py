from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import (
    KAnnoBasis,
)

# the authored pattern catalog keeps the canonical top view with positive zero entries
KPatAnnoTop: KAnnoBasis = ((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0))

# the live angle and count displays require the canonical back orientation
KPatAnnoBack: KAnnoBasis = ((-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, -1.0))

# pitch in the reversed top profile is visible in its canonical left annotation
KPatAnnoLeft: KAnnoBasis = ((0.0, 0.0, 1.0), (0.0, 1.0, 0.0), (-1.0, 0.0, 0.0))
