# Saved revolve rows can be sparse

An untouched cache-free revolve has four live contour-point rows in
the layout used by its analytic builder. A native save can keep retired
line and point rows. In the disclosed Front and Top saves, directly
calling the cold meridian builder with the saved profile raises
`KeyError(3)` because the cold order indexes the compact contour and the
saved point table uses sparse native indices.

Keep the selected active partition and rollback history in the saved
read path. Validate the native topology and bind the body name after
that check. Exercise analytic geometry through separately generated
cache-free inputs.
[Disclosed saved reads and generated cold controls](../../../../../../re/solidworks/records/PrincipalRevolveReader2026.md)
