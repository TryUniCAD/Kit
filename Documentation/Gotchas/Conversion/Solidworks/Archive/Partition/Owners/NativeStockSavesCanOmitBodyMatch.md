# Native stock saves can omit BODY_MATCH

SOLIDWORKS 2026 SP05.2 opened and rebuilt two model-generated ordinary
blind stocks. Both clean native derivatives have nonzero `moAtom_c.f180`
and `f1b0`, while the owning kernel bodies omit `BODY_MATCH`.

The stock research inspector binds the actual linked creator output and
Config-0 atom to the closed body through `ATOM_ID_2001` and
`LAST_BODY_MODIFYING_FEATURE_ID`. It also checks the implicit name, all
eight measured vertices, and all six face creation identities. A
present `BODY_MATCH` retains its existing validation. These observations
do not supply a rule for assigning a missing kernel stamp.
[Exact native and offline evidence](../../../../../../../re/solidworks/records/EdgeFilletStockAcquisition2026.md#native-and-linked-outcomes)
