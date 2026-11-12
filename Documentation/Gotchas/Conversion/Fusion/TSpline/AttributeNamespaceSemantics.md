# TSM numbered attributes are not editor selections

An external structural parser labels `100edges`, `100verts` and `50000grip` as editor selection records. Native RTTI and virtual ID getters prove different owners: namespace 100 is `tskern::ExCrease`, namespace 50000 is `tskern::ExSmartGrip`, and freezing is a distinct namespace 50001.

A native interior-edge crease changes the namespace-100 edge set and can add compound secondary smart grips. Treating these records as disposable UI selection loses surface semantics. Preserve typed crease edge/vertex sets and smart-grip indices, including a present empty crease extension.

[Static evidence](../../../../../re/Fusion/Reconstruction/TSpline/FieldEvidence.json) and [native crease contrasts](../../../../../re/Fusion/Reconstruction/TSpline/CreaseInventory.json) record the class IDs and geometric correspondence.
