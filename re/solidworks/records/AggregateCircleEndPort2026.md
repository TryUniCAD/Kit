# Measured fixed-centre circle end conditions on the current SDK

Task `B04-SW2026-CIRCLE-END-WRITE` in PR #121. The circle preparation,
typed geometry and measurement leaves are owned by the circle end-condition
workstream. The aggregate owner owns public dispatch. Base
`133d616e82251e11ddd99c5b2e0376d8fb488830` already has the shared generative
circle constructor, the linked end/driver owners and the registry staging
transaction. The measured nested assembly scope in #236 is distinct. Earlier
circle delivery #239 supplies a narrower cold Front diameter readback and
re-publication proof.

## Admitted scope

The disclosed cohort uses one actual analytic circle, a fixed centre,
one radial driving length, one native boss, one active configuration and
the measured canonical supports. Baseline construction already reproduces
each entire file. The baseline default strict geometry route admitted only
the Front diameter candidate from this cohort.

| Authored request | Support and radial owner | Actual native end |
| --- | --- | --- |
| radius | Front radius D1 | Forward blind |
| diameter | Front diameter D1 | Forward blind |
| reverse-right | Right diameter D1 | Reversed blind |
| mid-top | Top radius D1 | Mid-plane, total D1 |
| two-front | Front diameter D1 | Forward D1 and opposite D2 |
| two-rev-top | Top radius D1 | Reversed D1 and opposite D2 |

The shared profile rule retains the existing four pre-writer locked
combinations from [the original circle lifecycle](SdkOriginalCircleNative2026.md)
and [the paired end-condition receipt](../measurements/2026/SdkPairedEndConditionsNative01.json).
The two disclosed native receipts add the other five mode combinations.
The old blind strict reader retains its original positive normal guard. The
new geometry modes and both multi-end modes require the complete canonical
basis after verifying the actual datum and the stored sketch transform.
The existing driver, body creator, end-object and actual owning parent
checks still govern admission. Two directions keep their native first and
second owners and order. Each driver edits its own direction. Through-all,
selected terminations, offsets, arbitrary frames and cut/thin/draft states
are outside this profile.

## Exact publication leaf

The leaf selects the same shared typed preparation used by the prior
model-only probes and resolves the actual transaction destination. Pass
`solidworks_native_measurement` with `written_at` and a `receipt` containing
the exact UTF-8 terminal report text in `native_report`. For a stream, use the
measured Windows logical locator in `final_destination`. For a path, the
actual final destination controls the logical locator. The scoped POSIX
self-locator translation was exercised against the reported Windows
candidate path for all six disclosed requests.

The four report hashes bind immutable passing evidence from SOLIDWORKS
2026 SP05.2, build `34.5.2.0604`. The candidate must match its unique named
measurement case and complete file hash. Report identity authorizes
publication after regeneration and supplies zero archive fields. The paired
report authorizes the exact generated hashes from its successful native
lifecycle. Its two historical H03 saved-reader failures are separate from
those native stages and remain part of the original evidence.

Four locked case records were authenticated from redacted reports in this
tranche. The protected original/request data was never consumed. Current
host publication was exercised with the six independently disclosed requests.

Normal dispatch requires two changes after existing more-specific routes,
including any independently qualified offset-plane route.

1. In `Core/Writing/CanWritePart.py`, import `HasCircWrite` and
   `CanWriteCircle` from `Core.Writing.Circle.CanWriteCircle`. After the ellipse
   route and before B-rep/import/generic fallback, return
   `CanWriteCircle(DocumentValue, TargetValue)` when
   `HasCircWrite(DocumentValue)` is true.
2. In `Core/Writing/EmitNativeMut.py`, import `HasCircWrite` and
   `EmitCircMut` from the same circle writing package. After the ellipse or
   independently qualified offset-plane route in `EmitFreshMut`, return
   `EmitCircMut(DocumentValue, TargetValue, OptionsValue)` when
   `HasCircWrite(DocumentValue)` is true.

The normal dispatch verification used an isolated copy of `src` with those
two additions. Production activation requires aggregate integration.

## Process evidence and exit

Run `python3.14 -I -B re/tooling/sw2026/AuthorSdkCircleRequests.py /absolute/fresh/request-directory`.
For each request key in the table, run
`python3.14 -I -B re/tooling/sw2026/ProveCircleEndPort.py --case KEY --requests /absolute/fresh/request-directory --route leaf`.
To reproduce the ordinary entry evidence, run the same six independent
processes with `--route public --sdk /absolute/isolated/source-tree/src`,
using a source copy with the two documented selections. The re-run loads
only authored requests and tracked disclosed receipt texts before installing
the process guard. Native applications and saved CAD bytes are absent.

The [host receipt](../measurements/2026/AggregateCircleEndPort01.json) binds
the exact reconstruction sources, authored requests, accepted complete file
and stream hashes, actual routes and results. Twelve fresh Python workers
record 72 exact generated outputs, 24 strict reads, 144 publication refusals
and 24 model-scope refusals with zero runtime input-file reads. The full
reads preserve one linked analytic cylinder, two periodic rim edges, three
faces, signed axial bounds, volume and surface area to six significant
figures, and centroid within the measured comparison tolerance. Driver
and source-ownership checks run in both strict modes.

These are cold native-to-neutral SDK results plus measured publication
from complete authored neutral input. The archived source and edited-save
lifecycle of the four disclosed end-condition cases was independently
established in [the previous native and SDK study](SdkCircleEndConditions2026.md).
General native-saved-to-native republication remains open.
The common cold readback projection handles line bosses or equations.
It cannot presently map the actual circle-centre point and its relation back
to an authored centre subelement and verify both radial and complete end
driver wire values. The earlier #239 Front-diameter branch needs that
proof on the aggregate representation before widening the native-source
gate. Arbitrary parameter edits remain exact-output dependent.
