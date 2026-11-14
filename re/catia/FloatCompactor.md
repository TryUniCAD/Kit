# CATIA float compactor

## Finding

`SurfacicReps` surface carrier parameters are plain big-endian `f32` values, not
`CATFloatCompactor` output. The ten trimmed-face bounds are plain little-endian `f32` values.
`CATFloatCompactor` is used elsewhere, for example the Nurbs control-point predictor in
`CATAdvancedMathematics.dll`.

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

## Selector status

`GetLeadingZerosCount` at `0x18009bf70` counts the 32-bit leading zeros of the delta:
`0x1 -> 31`, `0x80000000 -> 0`, `0x10000 -> 15`. A Python model of the literal and equal
branches round-trips:

```text
literal seq 3f490fd840f0000040866666c02000005368d4a500000000
got [0.7854, 7.5, 4.2, -2.5, 999999995904.0] match True
```

The delta selector is still inconsistent under static reading. The reader computes
`width = 0x20 - (S & 0xffff)`, while the writer computes `S = 2 * (0x20 - leading_zeros) | sign`
and writes 58 bits where the reader reads 59. A synthetic writer/reader round-trip fails to
terminate with those widths. Settling the selector needs a dynamic trace or an independent
decompression sample, not more static reading.

`re/catia/tooling/BitStream.py` reproduces both bit-buffer state machines. It round-trips the
literal branch and reproduces the leading-zero counts, but no tested selector/last-field
combination round-trips the delta branch.

## Double variant

`ReadDoubleWithRef` at `0x18009b590` and `WriteDoubleWithRef` at `0x18009b7b0` are the 64-bit
counterparts. They show the same shape and the same one-bit discrepancy:

- reader reads the selector with `ReadBits(0x3a)` (58 bits) and computes `width = 0x40 - S`
- writer writes the selector with `WriteBitsCleared(S, 0x39, 0x40)` (57 bits) where
  `S = 2 * (0x40 - leading_zeros) | sign`
- the last field is written with `want=0`, `capacity=0x3f - leading_zeros`

A synthetic double round-trip over four selector/last-field combinations scores 0/20. The
doubling in the writer and the missing halving in the reader cannot both be right, so the
selector still needs a dynamic trace.

## Tessellation coordinate caller

`CATSplineCompactor::HandleArray` at `0x18009cb00` in `CATGeometricObjectsCGM.dll` is the caller
that builds the tessellation coordinate table. It calls the double compactor through these IAT
slots:

| Slot | Import |
| --- | --- |
| `0x1dd718` | `ReadDoubleWithRef` |
| `0x1dd720` | `WriteDoubleWithRef` |
| `0x1dd728` | `ReadDoubleStandard` |
| `0x1dd730` | `WriteDoubleStandard` |

`HandleArray` builds the reference `Number` from a spline prediction at `rsi`, then reads or
writes one double per coordinate against that prediction. So the shared tessellation coordinates
are compressed by the double compactor, not the float compactor. Decoding them is blocked on the
same selector.

`GetComputedRef` (`0x9be00`) and `GetComputedRefWithSize` (`0x9be30`) only build the spline
prediction. They do not contain the selector. A systematic search over 64 combinations of
selector width (57/58), writer selector formula (four variants), reader width formula (four
variants), and last-field width (two variants) found no round-trip. The selector is entirely
inside `ReadDoubleWithRef`/`WriteDoubleWithRef` and cannot be settled by static reading.

## Harness blocker

A dynamic harness was attempted in the Parallels Windows 11 VM. The VM is ARM64
(`PROCESSOR_ARCHITECTURE=ARM64`), while `CATMathStream.dll` is x86-64. The ARM64 PowerShell
cannot load the x64 DLL: `LoadLibraryEx` returns error `193` (`ERROR_BAD_EXE_FORMAT`). The VM has
no x64 C compiler, no x64 Python, and no x64 PowerShell. Building the harness needs an x64
toolchain installed in the VM.

## Harness result

An x64 Python 3.12.7 was installed in the VM. `re/catia/tooling/CompactorProbe.py` loads
`CATMathStream.dll`, constructs `CATMathStreamImpl` over a memory buffer, constructs
`CATDoubleCompactor`, and calls `WriteDoubleWithRef` then `ReadDoubleWithRef`.

The writer runs and produces streams. The equal branch round-trips. The delta branch does not:
the reader returns the reference value, which means its selector read is zero. Measured streams:

```text
value=1.5 ref=1.0 stream=00000000000000d00000000000000000 read=1.0
value=4.2 ref=4.0 stream=00343333333333c10000000000000000 read=4.0
value=-3.25 ref=-3.0 stream=00000000002800ff0000000000000000 read=3.0
value=2.0 ref=2.0 stream=00000000000000000000000000000000 read=2.0
```

The writer places the selector in the first 8-byte word; the reader's `ReadBits` returns zero
for it. The read-side `CATMathStreamImpl` setup is not consuming the buffer, so the harness needs
its read position and buffer fields corrected before the selector can be measured.

## Measured selector

The read-side setup was fixed: the read `CATMathStreamImpl` must keep `0xb0 = 0x1c` (read mode),
and the compactor flow is `0` for write and `1` for read. With that, the harness round-trips a
delta value: `value=1.5 ref=1.0` reads back `1.5`.

`re/catia/tooling/ReadBitsProbe.py` reads the selector directly from the stream
`00000000000000d0...`:

```text
selector 0x34
bits pos 6
bits buf 0xd000000000000000
impl pos 8
```

So the reader's selector is `0x34 = 0x40 - 12`, and `width = 0x40 - 0x34 = 12`, which equals the
leading-zero count of the delta. The writer's selector is `2 * (0x40 - leading_zeros) | sign`,
written as 57 bits; the reader reads 58 bits and gets `0x40 - leading_zeros`. The one-bit
difference is the alignment, not a contradiction.

The selector formula is therefore:

```text
writer: S = 2 * (0x40 - leading_zeros) | sign, written as 57 bits
reader: S = ReadBits(58), width = 0x40 - S = leading_zeros
```

`re/catia/tooling/ReadFieldsProbe.py` reads the full field sequence from the same streams:

```text
1.5/1.0   S=0x34 pos1=6 width=12 D=0x0 pos2=7 M=0x0            pos3=58
4.2/4.0   S=0x30 pos1=6 width=16 D=0x0 pos2=7 M=0x4ccccccccccd pos3=54
-3.25/-3.0 S=0x3f pos1=6 width=1  D=0x1 pos2=7 M=0x2005000000000000 pos3=5
```

So the reader is:

```text
S = ReadBits(58)
if S == 0: return reference
if S == 0x3f: return ReadBits(64) as a literal double
D = ReadBits(63)          # sign: 0 adds, 1 subtracts
width = 0x40 - S
shift = 0x8000000000000000 >> width
M = ReadBits(width + 1)
mask = shift | M
return base - mask if D != 0 else base + mask
```

For `1.5/1.0`, `mask = 0x0008000000000000` and `base + mask = 1.5`. For `4.2/4.0`,
`mask = 0x0000CCCCCCCCCCCD` and `base + mask = 4.2`. The `-3.25/-3.0` case takes the literal
branch (`S = 0x3f`).

The Python `BitReader` in `BitStream.py` still does not reproduce the DLL's `ReadBits` field
values, so the decompressor is measured but not yet ported.

## Ported decompressor

The divergence was the `ReadBits` mask. The DLL does `shl want; shr want`, which keeps the low
`64 - want` bits, not the low `want` bits. With that corrected, `BitStream.py` reproduces the
DLL's field values and the decompressor round-trips the measured streams:

```text
double 1.5/1.0 1.5
double 4.2/4.0 4.2
double -3.25/-3.0 -3.25
```

The literal branch reads `ReadBits(0, 0x40)` (all 64 bits). The delta branch reads
`ReadBits(0x3f, 0x40)` for the sign (1 bit), `ReadBits(width + 1, 0x40)` for the low mask bits,
and reconstructs `base ± (shift | low_bits)`.

## Coordinate lane entry point

`CATSplineCompactor::StaticUnstream` at `0x9cf90` in `CATGeometricObjectsCGM.dll` is the entry
point for the coordinate lane. It constructs a `CATSplineCompactor` on the stack, copies the knot
vector fields, and calls `HandleArray` (`0x9cc50`), which reads one double per coordinate through
`ReadDoubleWithRef`.

The signature is `(CATMathStreamImpl* stream, unsigned int dimension, CATKnotVector* knots,
short ?, double* out1, double* out2, double* out3)`. Decoding the lane needs the stream position
at the coordinate block and the knot vector. Both are still unidentified.

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
- `ReframeParam` (`0x5510`) and `ReframePoint` (`0x5620`) are called from the Nurbs predictor cases at RVA `0x9aa5`, `0x9b86`, `0x9df0`, `0x9e2f`, `0x9f4b`, `0xa16c`, `0xa182`, `0xa2c2`.
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
