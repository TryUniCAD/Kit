# CATIA float compactor

## Finding

`SurfacicReps` carrier parameters are not plain `f32` values. They are compressed by
`CATFloatCompactor`. The ten trimmed-face bounds are plain little-endian `f32` values and remain
readable without the compactor.

## Loader evidence

| Function | Address | Observation |
| --- | --- | --- |
| `CATFloatCompactor::ReadFloatStandard` | `0x18009c030` | reads one bit field and returns it as a float |
| `CATFloatCompactor::ReadFloatWithRef` | `0x18009c220` | reads a 16-byte reference entry, a bit width, and a delta |
| `CATFloatCompactor::ReadFloatWithRef2` | `0x18009c070` | same shape for a reference array |
| `CATFloatCompactor::ReadDoubleWithRef` | `0x18009b590` | 64-bit variant |
| `CATMathStreamBits::ReadBits` | `0x18009e780` | bit reader |
| `CATMathStreamBits::ReadBitsUncleared` | `0x18009e7d0` | bit reader without clearing |

The reference entry is eight bytes of reference value and eight bytes of bit width. The reader
reconstructs a float from the reference exponent and mantissa, then adds or subtracts a masked
delta. The exact bit layout is not yet reduced to a writer rule.

## Corpus observation

The `SurfacicReps` header carries a reference `0.785398` and a scale `1e12`. The header float count
matches the compressed carrier-parameter population. The first cylinder carrier bytes are identical
across unrelated parts except for the radius field, which shows the compressor is deterministic and
not a per-file key.

## Workaround

The production reader uses the raw bounds and the trim vector. It does not decode the compressed
carrier parameters. This is lossless for the bounds and topology, but it does not recover the exact
cylinder origin, axis, or radius from the carrier lane. The reader records the raw surface record in
`NativeSurface` when the analytic reconstruction is not safe.

## Open work

1. Reduce `ReadFloatWithRef` to a bit-exact compressor and decompressor.
2. Confirm the reference and scale fields on a held-out corpus.
3. Emit compressed cylinder, cone, sphere, and torus carriers from neutral geometry.
4. Measure the emitted carriers in CATIA.

## Evidence

- `CATMathStream.dll` SHA-256 `712e258f9c39f552e52f441713719cc5f1d7bea61dfb1b29c642af7cfb24e01b`.
- REA Evidence `ev_2ee9396c241c4608971bb2aca143d9dbde7ebfa090aee20e2f600f049511798c` for
  `ReadFloatWithRef`.
- REA Evidence `ev_26156205587f2385bfc477c0210911b7a9e745ac684f1afc1d82287f577f2581` for
  `ReadFloatStandard`.
