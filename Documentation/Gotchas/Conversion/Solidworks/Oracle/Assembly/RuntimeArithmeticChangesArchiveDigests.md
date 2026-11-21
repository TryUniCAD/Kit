# Runtime arithmetic changes archive digests

An exact generated archive hash is not automatically portable across Python/runtime installations. A disclosed SOLIDWORKS perpendicular preflight used unchanged source and request bytes but produced different complete host/guest files.

The [typed arithmetic record](../../../../../../re/solidworks/records/PerpendicularMateRuntimeArithmetic2026.json) identifies all differences. Eight `moView_c.f368.f08` small diagonal coefficients differ by two ULPs, repeated in both files, because the observed cosine differs by one ULP before unchanged quaternion row normalization. One `moPlaneRef_w.f100.f60` projection differs by one ULP: the three products are identical, but Python 3.12's built-in float summation returns the accurately compensated result while the host's sequential sum returns the adjacent double. The [Python reference](https://docs.python.org/3.12/library/functions.html#sum) documents the version change.

All other typed fields, map/node aliases, array lengths and stream topology remain exact for this disclosed fixture. Changing stable generator math or patching saved output would obscure the actual cause. Preserve both raw outcomes, map each differing value to its formula, and commit separate complete disclosed preflight identities when the variation is independently bounded. Require deterministic repeat in the actual execution runtime and fingerprint that runtime before hidden exposure. Native geometry/semantic acceptance remains an independent gate.

The [perpendicular method](../../../../../../re/solidworks/records/PerpendicularMateBlindMethod2026.md) follows this procedure and keeps the original host baseline. Its runtime identities are verification metadata; generation continues to consume neutral input alone.
