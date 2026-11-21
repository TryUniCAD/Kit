# Ordinary revolve end-mode sources in SOLIDWORKS 2026 SP05.2

Task `B04-SW2026-REVOLVE-ENDS`, owned by the PR #121 takeover. The source authoring isolates the native Mid Plane and Two Directions feature shapes before writing either mode. The pilot uses one offset rectangular contour on the Top plane, one ordered construction axis and identical D1 across four vendor-authored sources. The reverse trial changes the Two Directions reversal flag. [Discovery receipt](../measurements/2026/RevolveEndSourceDiscovery01.json)

## Authoring and inspection

Extract the six files named in the receipt's `tool_sha256` from its exact source revision into an external working directory. Use the Windows Python with pywin32 through `prlctl exec --current-user "Windows 11"` and run `AuthorRevolveEnds.py` with the job path. The runner uses SOLIDWORKS `SldWorks.Application.34` and confirms executable build `34.5.2.0604`, its digest and its x64 PE machine before authoring or editing. The registered SwConst library is version 34.0. The job pins the external specification and the healthy ordinary full-revolve control by hash. Discovery and held-out authoring have independent jobs and private output roots. [Native observer](../../tooling/sw2026/AuthorRevolveEnds.py) · [Creation API](https://help.solidworks.com/2024/english/api/sldworksapi/solidworks.interop.sldworks~solidworks.interop.sldworks.IFeatureManager~FeatureRevolve2.html)

The specification contains a split and named cases. Each case defines its principal plane, rectangular radial and axial intervals, translated axis and endpoints, revolve mode and direction, and distinct initial and edit angle values. The native lifecycle records the feature tree, clean open and rebuild, parameter owner, body count and mass properties. Each angular driver is edited individually. The worker saves a separate derivative, checks the original hash, and reopens the derivative in a new application process. Healthy pinned controls bracket the batch. Keep detailed held-out records and files in the private oracle custody until the writer and acceptance procedure are frozen.

## Measured source semantics

| Case | COM type | Editable display | Total sweep |
| --- | ---: | --- | --- |
| One Direction | 0 | D1 | D1 |
| Mid Plane | 1 | D1 | D1 |
| Two Directions | 2 | D1, D2 | D1 + D2 |

For a selected ray and effective axis, the Mid Plane sweep occupies `[-D1/2,+D1/2]`. The Two Directions sweep occupies `[-D2,+D1]`. The two unequal directions preserve both parameter values, names and independent edit behavior under reversal. In the pilot, reversal mirrors the transverse centre of mass with identical one-body geometry, volume and surface area. The symmetric source exposes zero for the second API angle and no second driving display. The numeric receipt records the analytic volume, area and centre for each completed observation.

The initial discovery recorded 250 passing numeric checks in 13 distinct native processes. Its source-level result is incomplete. The Mid Plane source opened, rebuilt and accepted a D1 edit. A live observer collided with replacement of its phase receipt before the edited derivative saved. Both controls and the other three full source lifecycles passed. The initial runner also tested all auxiliary SOLIDWORKS process names for postflight idleness. The corrected predicate checks the actual application process and owned lifetime handles. [Receipt replace failure](../../../Documentation/Gotchas/Conversion/Solidworks/Oracle/Process/LiveReceiptReadsCanBlockReplacement.md)

The controlled recovery pins the same Mid Plane source and original authoring receipt. Its two new candidate processes complete 38 numeric checks over the D1 edit, derivative save and fresh reopen. Both newly launched controls pass, the original source hash is unchanged and the application postflight is idle. The reused authoring receipt adds a fifth distinct process to the recovery's provenance. [Recovery receipt](../measurements/2026/RevolveEndSourceRecovery01.json)

The disclosed stream replay binds all four modes to the actual modern `moRevEndSpec_c` words, including the single retained Mid Plane display and two Two Directions displays. Eight guarded SDK workers reproduce the paired linked streams exactly. The existing semantic reader still refuses the two new modes. [Saved end owners](OrdinaryRevolveEndModes2026.md)

These are vendor-authored research sources. They add zero generated outputs and zero FCStd qualification credit.
