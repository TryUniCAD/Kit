# Native edit and save of a generated distance mate

The disclosed distance mate passed the driving edit, rebuild, synchronized save
and fresh reopen on SOLIDWORKS 2026 SP05.2 build `34.5.2.0604`.
Both A18 controls passed. The run used four distinct native processes and
zero held-out inputs. [Native and typed receipt](../measurements/2026/GeneratedDistanceMateEditNative01.json)

The guarded writer regenerated the original assembly and child at fresh
encoded paths from revision `c4fda5661f92ed77d8b743be0d1940035bdd50fa`.
It changed only the two authored paths and recorded zero runtime input reads.
The trial expected a vertex-authored child with one boss depth and no named
sketch dimensions. The earlier exact-path observation remains recorded with
its original failed sketch assertion. [Prior exact-path observation](GeneratedDistanceMateNativeOpen2026.md)

| Native observation | Result |
| --- | --- |
| Open at the encoded paths | Two resolved occurrences, open status 0/0, and the authored `0.071375 m` driving distance |
| Edit and rebuild | `SetSystemValue3` status 0 and generated D1 of `0.088125 m` |
| Endpoint and placement | Both ordered Right Plane identities and the fixed occurrence persist. The moving occurrence retains its 47.312° rotation and translates a further `0.01675 m` along X. |
| Rebuilt and reopened geometry | Two bodies, `1.46484375e-5 m³`, `0.00484375 m²`, and centre near `(0.0596875, 0.00221360, 0.01564435) m` agree with the analytic result. |
| Native saves and reopen | Save child, then parent. Each returns `[true, 0, 0]`. The parent save preserves the saved child hash and update stamp. A fourth process supplies the final control after the fresh candidate reopen. |

The readback verifies the saved file hashes and exact typed Config-0,
ResolvedFeatures and MatesList reconstruction. The decoded mate owns
the edited length and resolves persistent occurrence IDs 17 and 18
to child datum ID 16 on each occurrence. The readback also verifies
the moved occurrence's translation directly from the saved graph.
[Host saved-file checker](../../tooling/sw2026/PrepareDistanceMateEdit.py) · [Native observer](../../tooling/sw2026/InspectDistanceMateEdit.py)

This trial qualifies only the measured disclosed edit and persistence.
Held-out mate qualification and public adapter writing remain open.
