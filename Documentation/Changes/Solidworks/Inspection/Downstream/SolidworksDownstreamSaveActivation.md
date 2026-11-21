# SOLIDWORKS downstream save activation

The [exact-build source checkpoint](../../../../../re/solidworks/records/DownstreamSaveActivation2026.md) binds a conditional call in `uiModelDoc_c::saveDocument` that sets application downstream state before `uiBaseDoc_c::OnSaveDocument`. It records actual document, environment, model and direct-child predicate guards, the application setter virtual bridge, original function extents and hashes.

Use this as a source boundary for tracing the subsequent save route. The internal setting is known only as `RegKey_e(0x5f2)` with caller fallback zero. No preference value, fresh application default, standalone stream creation or store context is inferred. A table-reference candidate is explicitly refuted as constructor evidence because it is the exported destructor.

Verification was read-only original-PE metadata and bounded instruction inspection. No VM, CAD, COM, license action, hidden payload, saved CAD read, test or product execution occurred. Native loadability, usability and held-out acceptance remain unqualified.
