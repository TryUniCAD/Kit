# Publish measured SOLIDWORKS full-ellipse bosses

The SDK can generate an ordinary free full ellipse on the canonical Front
Plane with a single forward blind boss, active `Default` configuration and
live D1. The constructor takes authored neutral geometry and uses the same
part profile allocation, headers, counts, configuration and stream writers as
the ordinary line profile. It creates an empty body map under the measured
ellipse manager context. No saved part supplies construction data.

Use the normal `write_document` or direct part writer with the exact original
logical Windows locator and a `solidworks_native_measurement` envelope. Its
`written_at` is the original creation epoch and `receipt` is the parsed
[ellipse report](../../../../re/solidworks/measurements/2026/SdkColdEllipseReceipt01.json).
The complete emitted bytes must have a single matching passing case with
healthy controls, clean native edit/save/reopen and a live D1. The measured
volume, area and centroid must agree with the model at the initial depth and
at the reported edited and reopened depths. The caller owns
the authenticity of the unsigned receipt. Stream publication uses an empty,
seekable, writable stream. File publication requires a native Windows destination and its
actual locator to match the measured locator. Other compressed encodings require separate
native evidence even when the clear streams match.

Strict SDK reads of this cold archive prove the linked Front datum, exact
ellipse point/seam roles and actual D1, then verify all ten clear streams from
the recovered typed semantic model. The result retains one editable ellipse,
its boss and the linked solid. Re-export of that same strict readback uses
the preserved geometric stations and compares the entire regenerated strict
neutral document, including its topology and provenance, before the normal
per-artifact publication gate. With B-rep enabled, the SDK constructs two
planar caps and a rational swept boundary. Raw native geometry extraction,
alternate supports, constrained conics and additional features remain outside
this scoped reader and writer. The strict reader refuses known rebuilt or
edited saved ellipses explicitly when their additional owners lie outside
its verified cold profile.

The [disclosed integration proof](../../../../re/solidworks/records/SdkColdEllipsePromotion2026.md)
reproduced the two measured complete archives through the normal and direct
stream paths with zero runtime file reads, strict path and stream refusals,
and two preserved native read controls. It also checked the analytic geometry
against each existing SOLIDWORKS 2026 SP05.2 cold observation. Hosted
regression covers the same independent neutral inputs and keeps the exact
publication gate active on each compression runtime.
