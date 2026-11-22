# Axis box support requires the linked profile

The early SOLIDWORKS index can identify the sketch and its three axis labels
while reporting a provisional Front-plane support. The attached box actually
uses a Top-plane sketch, a reversed blind height and an independent
origin-coincidence object. It owns its named result through a Config atom
referenced by the producing boss. A typed reader must bind these objects before
constructing the body or claiming that its three axes have usable parents.

The strict signed-box route follows the actual profile and atom aliases, validates
the active end and then checks each axis's ordered wrappers against the two
physical datum planes. Its design-only mode keeps the same signed drivers and
selection paths through neutral JSON.
[Exact ownership and guarded proof](../../../../../re/solidworks/records/MeasuredFreecadBoxMain2026.md)
