# Annular cylinder carrier sense and face sense are separate

An annulus has two cylindrical walls that share an axis. In the
disclosed SOLIDWORKS 2026 SP05.2 D19 active partition, both cylinder
carrier records use a negative sense. The outer face has negative
sense and the bore face has positive sense. The effective geometric
wall senses are therefore positive and negative, respectively. Its
positive edge fin also belongs to either incident face depending on
the actual rim. Applying the plain cylinder rule of a positive wall
face and wall-owned edge head would misclassify this boundary.

Build the shared edge from its two reciprocal uses and choose the
actual positive fin. Preserve the physical loop chains. Interpret
wall orientation using the carrier and the face senses. The generated
bare local profile uses positive carriers and computes the wall face
sense from the validated neutral solid. Each closed circle has one
periodic seam in the neutral model and no physically stored vertex.
[Disclosed graph and generated evidence](../../../../../re/solidworks/records/AnnularLocalImport2026.md)
