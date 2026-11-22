# Measured planar mate bundle

The public registry writes two direct occurrences of one rectangular
blind-boss part. An ordered group contains an aligned coincident mate and an
aligned distance mate. The first occurrence is fixed. The native distance
driver starts at 42 mm and the child has two editable sketch lengths and one
editable blind depth.

| Generated member | Bytes | Streams | SHA-256 |
| --- | ---: | ---: | --- |
| `PublicDatumPrism.SLDPRT` | 8,714 | 10 | `b734fe2b8df59085860ae12f6dacabd363a4475f5399506efdce423d05c4ab7b` |
| `PublicPlanarPair2.SLDASM` | 10,392 | 12 | `d31950eb971645908a82c26ecb881880525a3c8aa9478bc971b065bc5bdcf2f4` |

The original exact SOLIDWORKS 2026 SP05.2 build `34.5.2.0604` measured four
separate processes and 360 numerical checks. Both controls passed. The worker
opened, rebuilt, edited the distance to 57.73 mm and saved the child before
the assembly. A separate process reopened the generated edit with zero
native open errors or warnings. The native trees retained 26 assembly and
25 child entries during the edit. The original summary recorded a readback
failure because the process had imported the COM observer. The independent
recovery verifies the original native phases together with the strict saved
readback on the original source revision.
[Original native phases and recovery](../measurements/2026/MeasuredPlanarPair/OriginalNativeRecovery.json)

The public publication proof recomputes both complete parts and all 22
streams from the neutral request. It checks the four phase identities and
checksums from the original oracle packet. The audit permits Python code
loading and stage creation. It observes zero input data reads from the
writer. The strict reopen of the regenerated assembly finds two occurrences,
one mate group, four endpoints and three child drivers. This measurement
covers the disclosed coincident-and-distance pair with one shared child.
Further native saved assembly variants use the established legacy reader.
[Neutral request](../measurements/2026/MeasuredPlanarPair/NeutralRequest.json)
[Exact output receipt](../measurements/2026/MeasuredPlanarPair/MeasuredOutput.json)
[Process proof](../measurements/2026/MeasuredPlanarPair/PublicationProcessProof.json)

```sh
python3.14 -I -B re/tooling/sw2026/ProveMeasuredPlanarPair.py \
  --packet "$PLANAR_PACKET" --output "$PLANAR_REPORT"
```
