# Coincident geometry does not prove reference identity

Matching position, shape, state, and owner does not identify a unique sketch entity when two distinct entities have those same properties.
A constraint attached to the wrong coincident point can therefore appear correct after native IDs are replaced by geometric descriptors.
Matching counts does not resolve this ambiguity.

The verifier now requires a unique geometric match for sketch entities and boundary vertices and edges.
Ambiguous identities produce unavailable checks and prevent semantic verification.
Face support has the same limitation: matching its producer and frame does not identify the selected face among multiple faces from that producer.
Face-attached sketches remain explicitly unverified until that identity is established.

Serialized CLI coverage duplicates points in both the decoded P03 document and its offline observation fixture.
It requires an unverified result even though both inventories still agree.
No local test or licensed application run was executed for this repair.
