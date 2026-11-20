# An automatic through-all request can retain the initially selected solid

In the measured SOLIDWORKS 2026 SP05.2 model, the circular through-all
tool initially intersects one of two separate solids. Creation with
`UseAutoSelect=True` resolves the stationary solid. Editing the second
boss depth moves the other solid into the same tool. It retains its
intact geometry, and selection access still returns only the stationary
solid. The same results occur after a fresh reopen.

Measure actual body ownership and geometry across an upstream edit
before translating an automatic creation argument into continuous
automatic scope. For this model the measured scope contains one
persisted stock owner.
[Controlled multibody result](../../../../../../re/solidworks/records/ThroughAllMultiStockScope2026.md#packet-03-native-result)
