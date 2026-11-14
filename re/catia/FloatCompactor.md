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

## Decoded `ReadFloatWithRef2` algorithm

`ReadFloatWithRef2` takes a `float*` reference array and emits one float per entry. For each entry
`ref`:

1. If `abs(ref) < threshold`, read 32 bits and emit them as a literal `f32`.
2. Else read a 59-bit selector `S`.
   - `S == 0`: emit `ref` unchanged.
   - `S == 0x1f`: read 32 bits and emit a literal `f32`.
   - Else: rebuild the base float bits from `ref`, read a 63-bit value `D`, read a variable-width
     mask, and emit `base - mask` when `D != 0`, otherwise `base + mask`.

The base float bits are:

```text
mantissa = (ref_low >> 40) & 0x7fffff
sign     = (ref_high >> 32) & 1
exponent = ((ref_high & 0xffffffff) + 0x7f) & 0xff
bits     = (sign << 31) | (exponent << 23) | mantissa
```

The mask is:

```text
width = (0x20 - (S & 0xffff)) & 0xffff
shift = 0x80000000 >> (width & 0xff)
read  = ReadBits(width + 0x21) when width != 0x1f else 0
mask  = shift | read
```

`ReadBits(dest, count, capacity)` calls `ReadBitsUncleared` and masks the result to `count` bits.
`ReadBitsUncleared` maintains a 64-bit buffer at `+0x08` and a signed bit position at `+0x10`, and
refills eight bytes at a time through `ReadUChar`.

The 63-bit value `D` is used only as a zero/nonzero flag in the subtraction branch. This is
unusual; confirm it on a traced span before implementing the writer.

## Verified base reconstruction

The base formula round-trips a reference entry to its source float:

```text
0.785398 -> 0.785398006439209
1.0      -> 1.0
-2.5     -> -2.5
7.5      -> 7.5
4.2      -> 4.199999809265137
0.0      -> 0.0
1e12     -> 999999995904.0
```

That confirms the mantissa/exponent/sign extraction, but not the stream bit order or the reference
array contents.

## Bit stream order

`CATMathStreamBits` keeps a 64-bit accumulator at `+0x08` and a signed bit position at `+0x10`.
`WriteBitsCleared(value, want, capacity)` left-aligns the low `want` bits of `value` into a
`capacity`-bit window, ORs them into the accumulator, advances the position by `capacity`, and
flushes eight big-endian bytes when the position passes 63.

A Python model of that writer round-trips 32-bit literals through a plain MSB-first reader:

```text
bytes 3f490fdb3fc000004020000040f00000000000007f7fffff0000000000000000
got   ['0x3f490fdb', '0x3fc00000', '0x40200000', '0x40f00000', '0x0', '0x7f7fffff']
match True
```

So the stream is a continuous MSB-first bit stream, and `capacity` is only the write window, not
the field width.

## Writer branch structure

`WriteFloatWithRef2` is the inverse of the reader. For each `(value, ref)` pair:

1. If `abs(ref) < threshold`, write the 32-bit value literal.
2. Else if `value == ref`, write 59 zero bits.
3. Else compute `delta = abs(value_bits - ref_bits)`.
   - If `delta >= 0x40000000`, write selector `0x1f` as 59 bits, then the 32-bit value literal.
   - Else write a 58-bit selector built from the leading-zero count of `delta` and the sign, then
     the shifted delta bits.

The selector formula is read from the writer but not yet confirmed by a trace. The reader's
`width = 0x20 - (S & 0xffff)` and the writer's `2 * (0x20 - leading_zeros)` differ by a factor of
two and one bit, so one of the two readings is incomplete.

## Caller and reference array

`CATAdvancedMathematics.dll` imports `ReadFloatWithRef2` and `WriteFloatWithRef2` from
`CATMathStream.dll`. The call sites are in `CATNurbsSurfaceCompactorF::HandleControlPoints` at
RVA `0xa6df` (write) and `0xa6fa` (read), and again at `0xa8a5` and `0xa8c0`.

The reference array is a predicted control point. `GetComputedCPIncremental` fills a three-float
temporary, and the compactor delta-codes the actual control point against that prediction. The
threshold is the constant at RVA `0x1d0524`, which is `1.0`:

```text
0x1d0524 0000803f f32le 1.0
```

So `abs(prediction) < 1.0` selects the literal branch. The same codec is used for surface
parameters through `CATGeoFloatCompactor::ReframeParam` and `ReframePoint`.

## Evidence

- `CATAdvancedMathematics.dll` SHA-256 `0805a61d91c275bc167abf88e83be586c7f4379a1e977170f64e8bd31af4bc4f`.
- IAT slot for `ReadFloatWithRef2` at RVA `0x1ce650`, for `WriteFloatWithRef2` at `0x1ce658`.
- Call sites at RVA `0xa6df`, `0xa6fa`, `0xa8a5`, `0xa8c0`.
- Threshold constant at RVA `0x1d0524` = `1.0`.

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
