# SOLIDWORKS two-direction boss revolve writing

Use the normal `solidworks.sldprt` writer with an ordinary rectangular
sketch on the canonical Top or Right Plane and a selected construction
axis. An `AngularRevolve` with `SideMode="two_sided"` carries independent
positive `AlongParameterId` and `AgainstParameterId` angular drivers.
The sweep must be a partial turn. The two drivers remain editable as
D1 and D2.

Two independent pre-writer locked parts pass native cold load, clean
rebuild, separate live angle edits, save and fresh reopen on
SOLIDWORKS 2026 SP05.2. They match the native feature trees and mass
properties. The Windows public registry, direct writer and named streams
reproduce the exact measured bytes with zero runtime input reads.
The same proof verifies a fresh output locator and eight refused inputs.
The integration suite exercises normal path and stream writes, strict
driver readback and the larger resolved stream for the second driver.

[Native and public proof](../../../../../re/solidworks/records/TwoDirectionRevolveParity2026.md)
