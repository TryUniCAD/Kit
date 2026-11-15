# Native length parameters in SOLIDWORKS 2026

Status: **binary schema identity confirmed; generated dimension acceptance pending**.

The runtime class `moLengthParameter_c` uses the existing double-parameter
serializer. It must participate in the node virtual dispatch and type hierarchy;
serializing a depth as an unrelated raw double would omit its live parameter.

| Item                               | 2026 `sldmodu.dll` evidence                                                                                                 |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| Runtime metadata                   | `0x4daefb70`, schema 1, object size `0x70`                                                                                  |
| Factory and constructor            | factory `0x4c1764c0`, length constructor `0x4c19bbe0`, double-parameter constructor `0x4c19baf0`                            |
| Vtable                             | `0x4d123bf0`                                                                                                                |
| Serialize at vtable `+0x28`        | `0x4c177fe0`, the shared double-parameter serializer                                                                        |
| Lightweight serializer at `+0x4b8` | `0x4c17adf0`, node lightweight data                                                                                         |
| Resolved serializer at `+0x4c0`    | `0x4b27e120`, no additional payload                                                                                         |
| Type parent                        | `moDoubleParameter_c`, then `moParameter_c`                                                                                 |
| Sketch dimension creation path     | `sgSketch::iAddValG2Constraint` `0x4c4b99a0`, H/V constructors `0x4c411360` / `0x4c4113b0`, parameter creation `0x4c820e10` |

The three vtable targets were independently read from the copied binary whose
SHA-256 is `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.
The grammar reuses `dm.moDoubleParameter_c.FUN_4c177fe0` and registers the length
class with normal node dispatch. Its numeric value remains authored; the optional
second value follows the existing presence flag and archive conditions.

This is not evidence of a complete display-dimension graph, solver state,
editable native output, or a successful target-application rebuild.
