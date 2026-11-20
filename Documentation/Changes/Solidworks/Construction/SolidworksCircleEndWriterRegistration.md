# Qualified SOLIDWORKS circle boss end modes

The normal SOLIDWORKS part writer accepts two additional millimetre
circle profiles. Both require an actual centre fixation and a driving
diameter on the canonical principal plane.

| Plane | Direction | End mode | Editable depth owners |
| --- | --- | --- | --- |
| Right Plane | Forward | Symmetric mid-plane | `D1` owns the total depth |
| Top Plane | Reversed | Two independent blind ends | `D1` and `D2` own their respective depths |

Call `write_document` with the neutral document and a matching
`.SLDPRT` basename. A binary destination uses an explicit
`final_destination`. Selection and preparation use the same gate.
The Front diameter forward blind and Top radius reversed blind
profiles reproduce their existing bytes.
[Existing blind profiles](SolidworksCircleWriterRegistration.md)

The [registered process proof](../../../../re/tooling/sw2026/VerifySdkCircleEndRegistration.py)
used the two frozen pre-writer neutral requests and their exact original
event. The normal infer-by-path writer and guarded stream writer each
reproduce the native-measured candidate bytes. All ten logical streams,
including the standard properties, have identical digests.
[Paired native lifecycle and centre readback](../../../../re/solidworks/records/SdkEndConditionHeldoutProtocol2026.md)

Seven isolated SDK processes make twelve public writes. They verify all
six promised native transfers, exact typed Config and Resolved readback,
zero runtime vendor reads, and both earlier blind profiles. Ten near
misses reject before staging. Two destination-policy refusals leave
the proposed output absent. The [process report](../../../../re/solidworks/measurements/2026/SdkCircleEndRegistration01.json) SHA-256 is
`dee4abf89ab7d24c88e6f8d2dfd52e4efa897d4ae9995cef2629535dfaf58171`.

This entry qualifies the two measured write profiles. The generated
readback covers semantic owners with B-rep and tessellation disabled.
Other end combinations, assigned materials, appearance and full
document metadata require separate evidence.
