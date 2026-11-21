# Uninitialized PE storage has no stored runtime vtable

A raw-file address reader must not turn the zero-initialized virtual tail of a PE section into bytes from a later file region.

The older private convenience helper accepted addresses through `max(VirtualSize, SizeOfRawData)`, then indexed the file without checking the raw extent. During bounded inspection of the session module's fallback environment storage, this could return unrelated file bytes as a purported pointer. That output was rejected before any class or receiver claim; it is not vendor object-state evidence.

The private proof generator requires the entire requested range to lie within `SizeOfRawData`. Runtime globals and fallback object vtables must instead be traced through constructors and setters, or observed in a separately authorized mapped-runtime capture. A section's loader-zeroed tail does not contain an already-constructed C++ object in the original file.

The independently grounded normal receiver in the style evidence comes from the app constructor's explicit wrapper allocation, vtable assignment and session registration. No fallback vtable is inferred from uninitialized file storage. Evidence is the independently rechecked raw-backed reads and `normal_ui_environment_registration` in the [style evidence](../../../../../re/solidworks/records/RadialStyleConstruction2026.json); no vendor bytes or listings are included.
