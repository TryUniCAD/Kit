# Read ordinary Mid Plane and Two Directions revolves

The strict SOLIDWORKS part reader projects the live angles of an ordinary
rectangular boss revolve. Mid Plane exposes one total `D1` in radians as
`symmetric_full`. Two Directions exposes independent `D1` and `D2` as
`two_sided`. Its reversed sense changes the effective axis and keeps the
same parameter ownership. The selected construction line and four contour
relations remain linked to their real sketch owners.

The reader uses the saved native body when present. For an admitted file
without a cache it computes the signed sweep from the same live angles and
follows the contour's actual line endpoints. Cold geometry requires the
complete allocated angular owner inventory to match the active display chains.

Four disclosed saved parts and four model-only files passed strict geometry
and history reads. The guarded comparison checked both cap boundaries,
positive driver IDs, volume, surface area and bounds against the authored
profile and existing native measurements. Eight one-sided reader views
retained their previous document digests. The new modes have evidence for
partial Top-plane cases, with a forward Mid Plane and both senses of Two
Directions. Full-turn and reversed Mid Plane cases remain outside this
measured reader scope.

[Reading guide](../../../../Reference/Research/Solidworks/OrdinaryRevolveReading.md) ·
[Guarded reader evidence](../../../../../re/solidworks/records/SdkOrdinaryRevolveEndRead2026.md)
