# Managed extrusion packets exclude through-all construction

## Expectation

The presence of a managed `EndSpecification_c` base and `BlindEndSpec_c` can suggest that a through-all extrusion is a blind packet with a different termination enum.

## Actual behavior

In the exact 2026 mixed-mode core, `ExtrusionPacket_c.CurrentEndSpec` returns null for native types 1 and 2 and for the default branch, including 9. It constructs the blind, mid-plane and selected reference-based variants separately. Its initializer likewise selects null for types 1 and 2. `BlindEndSpec_c.ApplyToModel` publishes a distance and then explicitly sets native type 0.

The native model's `deleteNotUsedDims` and `recreateNecessaryDisplayDims` both remove or avoid the active distance display for types 1–4 under the same environment predicate. This is a graph-ownership distinction, not proof that the application lacks through-all support.

## Workaround

Trace and measure the native COM command route for the actual operation. Author new vendor controls, capture feature-owned dimensions and correlate their native owners. Do not allocate a live blind distance just because the API accepts placeholder depth arguments. Keep the environment selector and through-all-both API normalization explicit until measured.

The [construction record](../../../../../../re/solidworks/records/ThroughAllConstruction2026.md) contains module hashes, method tokens, native addresses, confidence and evidence limits. The [source protocol](../../../../../../re/solidworks/records/ThroughAllSourceProtocol2026.md) keeps new held-outs separate from exposed historical designs.
