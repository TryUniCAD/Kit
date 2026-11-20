# Draft SOLIDWORKS rectangular solid import

The SDK write path admits one plain, axis-aligned rectangular solid from
a geometry-only millimetre document with one active configuration. Pass
the document and a `.SLDPRT` path to `write_document`. The prepared part
uses the destination name, retains the configuration name and generates
one BaseBody feature named `Imported geometry`.

The guard requires all eight distinct corners of the exact Cartesian
product of two coordinates per axis, six plane faces and twelve line
edges. The shared prism compiler checks the complete outward shell,
analytic carriers and linked trims before selection. Each face must
own its exact axis plane and coordinate. Both unit normal signs use
the shared oriented ring checks. The existing
periodic cylinder route retains its own checks. Source identity,
provenance, additional model state, alternate shapes and binary
destinations remain outside the admitted profile.

Two guarded host processes prepare the disclosed rectangular control
at its original logical destination and epoch. Both reproduce the
9,914-byte archive with SHA-256
`302c8e9b608e513a714ef3139c5f4fcc4e8033fedf4718b6591f4a2aff80a357`.
All 12 logical streams match the case that previously passed native
open, rebuild, save and fresh reopen. The recipe computes the authored
ambient light from the same creation event.
[Disclosed native lifecycle](../../../../re/solidworks/measurements/2026/GeneratedLocalBodyPartCompleted01.json)
· [Same-locator lighting comparison](../../../../re/solidworks/measurements/2026/GeneratedLocalImportLightingContrast01.json)

A separately authored signed rectangular solid passes the no-options
host staging path and default strict readback. The read verifies both
stored self locations, the closed boundary and its actual body,
feature and configuration owners. The write reports exactly two
native transfers, B-rep and configurations. The guarded exact and
staged preparation use zero runtime data reads. Twelve rectangular
refusals and fifteen existing periodic refusals pass. The refused
shapes include the earlier triangle, a trapezoidal prism with identical
element counts and a box whose face has a foreign loop. A plane shifted by
`2^-34 mm` retains the corner and topology counts and passes the shared
prism residual check. The exact face-plane check refuses it before output.
[Host verification](../../../../re/tooling/sw2026/imported_body_source/VerifyPublicBox.py)
The host report SHA-256 is
`5ed595144edd9ba39bb9fc79edd9c627629b84298d00a45ccdbf0c531a2dfda6`.

Fresh native acceptance of the no-options Windows route and bare
held-out cases remain pending. The earlier locked planar lifecycles
use attributed bodies and projected source labels.
[Locked geometry evidence](../../../../re/solidworks/measurements/2026/SealedImportedLocalGeometryNative01.json)
