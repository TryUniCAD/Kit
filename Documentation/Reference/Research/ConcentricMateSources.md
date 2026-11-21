# Author native concentric mate sources

This research method prepares independent SOLIDWORKS 2026 concentric assembly sources. It does not add concentric writing or qualify a conversion route. Read the [CAD criteria](../Operations/CadSuccessCriteria.md), the [RE playbook](../../../re/Playbook/README.md) and the [field record](../../../re/solidworks/records/ConcentricMateConstructionSources2026.md) first.

Use a Python 3.11 or 3.12 process. Keep licensed native modules and all packet outputs outside every Git checkout. Packet outputs must remain under the macOS home directory shared as `\\Mac\Home`; the preparer derives that explicit mounted identity. The tools use the pinned 2026 build and a previously qualified immutable control. Replace all example absolute paths with the approved local paths.

```sh
python -B re/tooling/sw2026/CollectConcentricEvidence.py --binaries /licensed/Solidworks2026/bin --output "$HOME/Documents/ConcentricNativeBinding.json"
python -B re/tooling/sw2026/PrepareConcentricMateSources.py "$HOME/Documents/ConcentricSourcePacket" "$HOME/Documents/Control.SLDPRT" --native-evidence "$HOME/Documents/ConcentricNativeBinding.json"
python -B re/tooling/sw2026/CheckConcentricSourceProtocol.py "$HOME/Documents/ConcentricSourcePacket/Source.json" --packet-sha256 SOURCE_SHA256 --output "$HOME/Documents/ConcentricHostCheck.json"
```

The preparer requires its 16 named tools together. Copy the nine unchanged helpers from the pinned baseline recorded in the field record; do not borrow files from a different runtime closure. The host packet holds independently authored D01–D03 only. It contains no hidden design, native hidden file or hidden observation. The control is used only for native brackets.

The VM owner verifies the exact packet and executes the arrays in `Recipe.json` serially through the approved `prlctl exec --current-user "Windows 11"` boundary. Run metadata first. It loads the registered 34.0 type libraries without starting SOLIDWORKS. Stop on a missing interface, method, enum or signature. The next guest-only seal phase creates H01/H02 on an explicit fixed guest drive and publishes only their combined hash. It does not publish their values.

For each case, run before control, author, fresh original reopen, fresh edited reopen, after control and lock. Always attempt the independent after control if a native case fails. A failed phase prevents that case's lock and later design exposure. Do not rerun a completed phase in place: retain its evidence and create an independently named successor packet. The source author owns only the CAD instances it starts and never controls licensing processes.

The author creates a real radial-driven circle boss, two occurrences, one cylinder-face concentric mate and independent STEP siblings. It verifies both valid slide/spin and depth persistence, full native trees, exact child ownership, body geometry and reference semantics. Locked cases exercise a valid axial slide, not a forbidden-spin rejection. Misalignment and other reference types stay outside the first scope.

The final source lock requires all five distinct native process identities, clean open/rebuild/save/reopen statuses, both healthy controls, immutable native and STEP siblings, exact parameters and reference/geometry agreement. Keep detailed H files in the guest. Only opaque identity, progress, status and artifact digests may cross to the host. A healthy source corpus enables subsequent writer research; it does not itself count as generated output acceptance.

The first native pilot stops on the registered size method. Use the
returned eight-value `EntityParams` array and retain the independent
geometry checks. The corrected cohort passes all twenty-five native
processes and locks the two guest-private originals. Run
`VerifyConcentricMateStreams.py PACKET OUTPUT --packet-sha256 SHA256`
for the six disclosed archive states. [Source change](../../Changes/Solidworks/Construction/Assembly/SolidworksConcentricMateSources.md) [Archive field and evidence record](../../../re/solidworks/records/ConcentricMateArchive2026.md)
