# Measured public SOLIDWORKS width-to-depth equation on main's writer

Task `B04-SW2026/equations-local-references`. The PR #121 takeover
delivery ports the cache-free Front Plane rectangle and local depth relation
to the standalone writer from main `c8d85d713dc357770115329e9f1bcb027dbfca4f`.
The legacy ordinary line loop, generic equation inspection and cached
geometry paths retain their previous scope. [Change entry](../../../Documentation/Changes/Solidworks/Construction/SolidworksMeasuredWidthDepth.md)

## Linked field boundary

ModelHeader seeds the configuration map. The one selected physical row and
the active aliases in CMgr must match the ordinary Config-0 identity.
`moPart_c.f9d0` owns `moRelMgr_c`, which contains one enabled
`moRelation_c`. Its target and dependency have distinct local components
bound to that part and exact matches to the live ResolvedFeatures
dimension handles. The target uses the forward blind boss's active D1. The
source uses the dimension on the actual horizontal width edge. The second
sketch distance is the independent height. The point/line graph verifies the
external Origin owner and the one actual origin coincidence. Four axis
constraints and both live distance constraints survive strict readback.
[2026 relation field evidence](https://github.com/TryUniCAD/Kit/blob/0167c3e33a045b82fb9ac17a5aa10560b2070ba8/re/solidworks/records/PartEquationConfig2026.md)

The normal part container, headers, configuration, definition, stream
emitter and persistent map machinery construct the complete file from the
neutral document and its specified output and epoch. The equation-specific
owner grammar activates only for this profile. The reference uses 28,811
Config-0 bytes and 12,247 ResolvedFeatures bytes, with final map counters
163 and 256. An independent width and sketch-label variation changes both
stream lengths and cannot publish under the reference's measurement.
[Revision-bound process receipt](../measurements/2026/SdkMeasuredWidthDepthMain01.json)

## Native and process evidence

The disclosed reference uses `C:\KitSdkCandidates\WidthDepthSameLocator04.SLDPRT`
and has dimensions 39.125 mm width, 17.375 mm height, and 19.5625 mm
depth before editing. SOLIDWORKS 2026 SP05.2 build `34.5.2.0604` admitted
both the plain and equation cases in separate open/edit/save and fresh
reopen phases. Both bracket controls passed. Changing width to 47.875 mm
left the plain boss at 19.5625 mm and moved the equation boss to
23.9375 mm. The six native lifetimes record 188 numeric checks. The
archived report binds the measured 9,157-byte reference SHA-256
`5783b3944d76563ae8143b8789a923f1b07fb4eb94f4b59fef50b6b80ac696b6`
and the saved derivative.
[Native comparison](../measurements/2026/SdkWidthDepthPreparationNative01.json)

A distinct pre-writer locked comparison established scoped local equation
behavior over four native lifetimes and 103 numeric checks. Its
metadata-only receipt is retained independently of the disclosed release
authority. [Prior held-out evidence](../measurements/2026/WidthDepthLockedEvaluationNative01.json)

The standalone process proof reads only the four pre-existing disclosed
JSON inputs and compact receipt before starting each of two workers. The
workers independently reproduce the complete measured file from neutral
intent and report zero runtime input reads. The direct writer and registry
publish the same exact bytes from authored neutral input and from strict
cold readback. The registry also publishes the complete staged host file.
Strict design-only and default reads agree on 19 projected timeline rows,
two driving sketch lengths and the live derived depth. The body has six
faces, twelve edges, eight vertices, and 13,298.5263671875 mm³ volume.
Config framing and relation-mode faults reject both strict reads and retain
a precise diagnostic for permissive inspection. Raw extraction reports an
absent saved cache. Stale evidence and models leave existing outputs
unchanged. [Proof method](../../tooling/sw2026/equations/ProveMeasuredWidthDepth.py)

```sh
python3.14 -I -B re/tooling/sw2026/equations/ProveMeasuredWidthDepth.py \
  --disclosed /path/to/WidthDepthSameLocator04 \
  --output /tmp/KitMeasuredWidthDepth.json
```

## Review regression and hosted coverage

The tracked queue model authors the same underlying portable document
from four contour points, two driving sketch parameters, the explicit
origin relation and the live boss equation. The reference freezes ten
decoded stream digests from the fully matched 9,157-byte output. The
queue launches the guarded workflow with that neutral model, the existing
authenticated native receipt and the ten stream digests. It exercises
direct and registry publication from both authored input and cold
readback. The host path case also exercises staging. Publication requires
the original whole-archive digest on every runtime. A runtime that emits
identical logical streams and different complete bytes reaches the
normal exact-output refusal before any caller output.

The shared Windows shard that collects `TestEqWin` uses the measured
part runtime setup shared by the bounded imported-body fixtures.
The pinned CPython 3.12.7 x64 path is required in that shard. The case
requires the original whole digest and four public stream publications.
Its report validation also requires an actual passing call for the
selected case. The ordinary suite still checks the exact decoded streams
and refuses different whole bytes on other compression runtimes.

A fresh local macOS process with CPython 3.12.14 and classic zlib 1.2.12
reproduced the measured 9,157-byte output, five host publication routes
and zero runtime input reads. All ten decoded stream digests matched.
The portable process report has SHA-256
`1caf5fe0971656d02c6f93279f6e34ea8534eb04c732c4a1ce0e83db186eb9cf`.
The hosted Windows 3.12.7 result is pending.

The independent 20.01 mm width case keeps the same locator, names and
epoch. Its strict geometry and design reads return 20.01 mm width,
17.375 mm height and 10.005 mm derived depth. The displayed width
recovers the authored value by dividing the live wire value by the
forward coefficient 0.001. Multiplication by 1000 produces the adjacent
binary64 value. Strict readback regenerates the edited model's exact
candidate bytes. The initial native receipt refuses this changed model
through both public stream entry points, leaving each sink untouched.

The disabled-mode case sets the typed relation word to zero on a fresh
in-memory candidate. It carries the same locator and formula text.
Strict geometry and design reads refuse it. Permissive design and raw
inspection keep the source digest and diagnostic and expose no live
derived depth. The separate /3 contrast changes the complete expression,
side text and divisor token. Generic inspection exposes the scanned /3
formula without claiming typed width-to-depth ownership. These synthetic
archive contrasts use the SDK only. SOLIDWORKS was never asked to open
them. [Review proof](../measurements/2026/SdkWidthDepthReview01.json)

The original native measurement establishes the live width edit and
reopen of the SOLIDWORKS-saved derivative at the actual measured event.
The scoped release authority covers one exact regenerated archive at its
encoded locator and epoch. Additional authored sizes, relocated output,
other formulas, saved geometry, assemblies and corpus completion need
separate acceptance evidence. Ordinary Skew and Step retain their own
guarded publication controls.
[Plain controls](../../tooling/sw2026/CheckMeasuredPartWriter.py)
