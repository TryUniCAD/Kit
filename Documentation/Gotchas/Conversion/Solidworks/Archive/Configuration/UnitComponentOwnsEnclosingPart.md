# The unit component references its enclosing part

Within the complete ordinary Config-0 graph, the tagged unit component
has its own map slot. Its embedded component owner's object tag references
the original part at slot 2. Using the current unit component as the owner
rejects valid native parts. The standalone component field probe has the
part itself as its frame owner.

Bind the complete graph's authenticated part root before reading or
writing the unit component. Both paths check the same actual object.
The separately linked ModelHeader self object at slot 3 also exists in
the map and has the same reference width. It cannot stand in for the part.
[Measured offsets and guarded refusals](../../../../../../re/solidworks/records/OrdinaryPartConfigGraph2026.md)
