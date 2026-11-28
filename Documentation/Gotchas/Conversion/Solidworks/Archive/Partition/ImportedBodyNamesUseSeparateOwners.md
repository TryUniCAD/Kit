# Imported feature keys and body labels have separate owners

The ordinary local import's storage key follows its native feature name.
Its implicit body label follows that name until the body receives an
explicit label. Three SOLIDWORKS 2026 SP05.2 contrasts retain the same
feature key after a separate body rename.

Use the resolved body atom's Unicode node name for the explicit label.
The local kernel's compatibility attribute contains `Casting O72` in the
measured save whose live body name is `Casting Ω72`.
[Native contrast](../../../../../../re/solidworks/measurements/2026/ImportedBodyNamesContrast01.json)
