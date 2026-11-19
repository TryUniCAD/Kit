# Null offset references preserve stored points

A null pattern offset reference leaves its associated stored point unchanged.

The exact 2026 parameter store calls `getOffsetPt_FromRef(f210, fa8)` and its `f238/fc0` counterpart. The complete helper returns zero immediately for a null reference and leaves the supplied point unchanged. The store then writes the persistent point's actual value. The [native record and metadata](../../../../../../re/solidworks/records/LocalLinearPatternStoreLifecycle2026.md) bind that branch and its callers independently of saved corpus values.

Preserve actual points during raw replay. Fresh generation needs the object's constructor, input and update rules. The adjacent serialized local vector and point get their zeros from the native local constructors. Native writer and held-out acceptance remain open.
