# Pin cylinder radial mode and parameter-name ownership

The research [binding tool](../../../../../re/tooling/sw2026/freecad_cylinder/PinCircleNativeBindings.py) reads only the exact pinned SOLIDWORKS 2026 model PE and emits numeric addresses, method hashes, virtual targets and small format vocabulary. It executes no vendor code and opens no analysis document.

The [record](../../../../../re/solidworks/records/FreecadCylinderNativeParameter2026.md) independently rechecks explicit radius versus diameter construction and distinguishes automatic `D1` naming from the actual stored parameter name. It identifies the existing SDK name constructor and the remaining circle and depth-keyword forwarding gaps. [Machine-readable evidence](../../../../../re/solidworks/records/FreecadCylinderNativeParameter2026.json) binds seventeen native method ranges, REA identity evidence and twelve SDK source dependencies. It also identifies the separate secondary-mask side effect of one resource-dependent native naming branch, without guessing the resource text.

No source primitive writer or shared SDK change is added. Custom-name edit/save/reopen behavior, name collisions, full source metadata and the other primitive parameter owners remain unqualified. See the [specific gotcha](../../../../Gotchas/Conversion/Solidworks/Profile/Dimensions/AutomaticCircleNamesAreNotWireConstants.md).
