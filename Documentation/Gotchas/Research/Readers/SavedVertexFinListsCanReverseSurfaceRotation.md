# Saved fin incidence lists can reverse surface rotation

The saved P03 active partition records a finite `next_at_vx` list
for each vertex. The list ends with a null reference. The surface
rotation follows a different pair of links and closes on the start.
At five of eight vertices the two orders are opposite. Both orders
cover the same three owner fins. The pocket-specific order comparison
refuses this part.

Validate the finite incidence list and surface rotation independently.
Check the vertex owner and exact fin set in each path. Preserve both
orders. Use the actual face loops when projecting oriented geometry.
[Saved owner graph](../../../Changes/Research/Solidworks/SolidworksSavedActiveOwnerResearch.md)
