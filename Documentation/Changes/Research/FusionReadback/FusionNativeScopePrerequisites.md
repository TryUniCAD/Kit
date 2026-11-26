<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Owned Fusion scope capture prerequisites

A07 native acceptance remains open.
This change prepares current-source capture without using the old endpoint or assigning a saved selection-policy meaning.
It follows local integrity repair `b475f94486272e6b7c4ea43a068b32376248026e`.

## Direction evidence

The fixed study already authors a negative through-all extent.
Recorded Fusion 2706.1.17 measurements showed the expected inward material removal, while `isPositiveDirection` returned true.
Changing authoring direction to satisfy that getter would reverse the working cut.

The [scope model](../../../../re/automation/PairedCaptures/ScopeControl/FusionScopeModel.py) now records the raw Boolean without interpreting it as world direction.
It measures the verified upper support cap before the Cut sketch.
It measures participant bodies immediately before the Cut.
The report retains both timeline markers.
The actual inward direction follows the verified cap normal, pre-cut body half-space and measured material loss.
Existing exact volume, centroid, bounds, topology, producer and target checks remain required.
The [offline consumer](../../../../re/automation/CutScopeEvidence.py) independently repeats those checks.

This is bounded evidence for the fixed separated-body study.
It does not define a general interpretation of the native flag.
A positive flag with wrong geometry still refuses.
The prior single-process exploratory observations do not establish accepted Phase A/B evidence.
See [the direction-flag gotcha](../../../Gotchas/Research/Fusion/ThroughAllFlagNeedsGeometry.md).

## Private runner configuration

The [bootstrap](../../../../re/automation/PairedCaptures/Runner/KitCaptureRunner/KitCaptureRunner.py) can now use an explicit adjacent `KitCaptureRunner.runner.json` file.
This owner-controlled file selects a private runner home:

```json
{
  "version": 1,
  "home": "/absolute/private/FusionRunner"
}
```

Create that home as an owner-only physical directory before loading the add-in.
Set directory permissions to `0700` and sidecar permissions to `0600`.
The sidecar must be a regular, single-link file owned by the effective user.
Its schema has exactly one version and home, with no duplicate fields.
Relative, missing, linked or publicly accessible homes refuse.
The sidecar is limited to 4096 bytes.
This option currently supports macOS only.

Place the ordinary `config.json` inside that private home.
Its existing `allowed_root`, `dispatch` and optional `startup` fields keep their current meaning.
The runner's queue and status files stay inside the selected home.
Its custom event identifier includes the SHA-256 of that physical home path.
Without a sidecar, the existing default home and event identifier remain unchanged.
No environment variable redirects this source authority.

Use the existing [startup provisioner](../Workers/FusionStartupProvision.md) to stage the committed bootstrap and manifest.
Keep the sidecar and runner configuration with their own immutable private setup receipt.
The startup profile continues to bind the installed bootstrap, manifest, provider, application bundle and installation.
The private sidecar is separate owner configuration, not a native qualification receipt.

Register the new private add-in through the public [Scripts.addExisting API](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_Scripts_addExisting.htm).
Retain the old add-in registration and files.
The public [Script API](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/core_Script.htm) supports checking its state and enabling startup for the new registration.
Use the supported controller, supervisor and [phase queue](../Workers/FusionPhaseQueue.md) for accepted capture.
Do not treat a direct script invocation or a status file as accepted readiness evidence.

## Verification before native capture

The private-home process suite executes the full bootstrap in child processes with disposable application protocol fixtures.
Twelve controls passed for private operation and malformed, linked, public, duplicate, top-level array or missing configuration refusals.
The revised inference suite passed 34 cases.
It accepts either raw Boolean flag only when the complete inward geometry and support-marker witness agrees.
Integer flags, late or Boolean support markers, wrong support normals/offsets and missing material removal refuse.
All 46 process cases passed in 10.24 seconds.
These fixtures do not call CAD APIs and cannot establish native acceptance.
Focused formatting, Ruff, steering, Mypy and Pyright checks passed before source freeze.

A separate read-only native probe reached Fusion 2706.1.17 and observed zero open documents.
No sign-in workaround or license change was needed.
The old runner was stopped and its registration did not run on startup.
No existing native document, registration or endpoint was changed by that inspection.
The embedded home frontend was reachable through the existing local research bridge.
macOS Accessibility inspection was unavailable; that did not prevent the read-only public API probe.

## Remaining acceptance

Freeze the committed source before provisioning a new installation and private A03 store.
Obtain that store's original parked assessment receipt, then attach its exact queued Phase A/B pair with `Resume.py`.
Retain healthy controls, source/input/archive pins, accepted outputs and full process identities.
Obtain a normal owned native exit and same-build fresh reopen.
The supervisor worker's zero exit status does not prove normal Fusion exit.
The current Darwin lifecycle observer explicitly leaves the native exit cause unverified.
A separate native status or diagnostic witness is required before calling that exit normal.

The fixed automatic and explicit-A+B cases intentionally have equal geometry and resolved target lists.
[Autodesk's input API](https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/fusion_ExtrudeFeatureInput_participantBodies.htm) documents an unset creation default.
It does not establish a distinct persistent automatic policy.
The [Extrude UI reference](https://help.autodesk.com/cloudhelp/ENU/Fusion-Model/files/SLD-REF-EXTRUDE.htm) describes recomputing selection while editing.
A separate black-box behavioral and saved-field contrast must distinguish or refute the persistent-policy hypothesis.
Keep every `observed_policy` null until that proof exists.
Validate any resulting rule on unrelated held-out designs without consuming P05.
A06b admission/comparison paths, shared registers, P02 separation and historical captures remain outside this change.
