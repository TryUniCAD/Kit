# The rim of a rectangular pocket owns two directed loops

A closed solid can have a face with an opening. In two SOLIDWORKS 2026
SP05.2 saves of an inward shell, the upper rim owns two Parasolid `LOOP`
records. The first follows the outside of the rim and links to the inward
opening. Both records identify the same `FACE` and the second `next` is zero.
The signed XY areas identify the two physical roles. The surface normal is
negative Z and the face sense reverses it, giving effective positive Z.

Preserve ownership and direction for each loop. Other measured native shapes
can store the hole first, so geometric containment still governs general
reading. The bounded generated rectangular pocket uses an exterior first
chain and an equivalent outward plane orientation.
[Two saved graphs and independent generated contrasts](../../../../../re/solidworks/records/LocalPocketTopology2026.md)
