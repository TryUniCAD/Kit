# Derived circle trims can round off zero

The generic Parasolid geometry builder derives an edge interval by measuring
its reconstructed endpoints against the analytic curve. For a proved
vertex-free local cylinder rim, the builder synthesizes the shared endpoint
at circle parameter zero. Projecting that point back onto a signed oblique
circle can return a tiny nonzero start parameter. The changed-radius host
control reports about −3.38 × 10⁻¹⁷ radians and a complete period.

After validating the actual two circular carriers, paired vertex-free fins
and closed cap and mantle loops, restore both intervals as exactly zero to
one full turn. The wire contains those complete periodic boundaries and
supplies no separate trim values. The geometry builder still checks endpoint
incidence, and the local reader still checks the closed topology.
[Local cylinder reader](../../../../../../../src/convert/adapters/solidworks/Core/TypedResolved/Geometry/LocalBody/Cylinder/ReadLocalCyl.py)
· [Signed oblique radius contrast](../../../../../../../re/tooling/sw2026/imported_body_source/VerifyLocalCylinderWrite.py)
