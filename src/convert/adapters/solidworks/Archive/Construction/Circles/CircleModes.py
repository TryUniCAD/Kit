# four original locked scopes retain their existing neutral admission boundary
KOrdCircModes = frozenset(
    {
        ("z", True, False, "blind", False),
        ("y", False, True, "blind", False),
        ("x", True, False, "mid_plane", False),
        ("y", True, True, "two_directions", True),
    }
)

# additional native measured circular profiles use the same fixed centre and signed end grammar
KMeasCircModes = KOrdCircModes | {
    ("z", False, False, "blind", False),
    ("x", True, True, "blind", False),
    ("y", False, False, "mid_plane", False),
    ("z", True, False, "two_directions", True),
    ("y", False, True, "two_directions", True),
}
