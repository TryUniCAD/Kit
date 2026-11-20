<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Early part visibility override can stall SOLIDWORKS shutdown

In private collector runs on SOLIDWORKS 34.4.1.1011, moving `DocumentVisible(false, swDocPART)` forward to cover the capture loop caused the owned application to remain alive after `ExitApp`.
All 25 discovery files and both controls passed observation in each run.
The collector refused the results after its 60-second exit deadline.
The same roster and order with the original collector completed and exited normally.

The timeout also occurred with command batching disabled, with visibility reset before exit, and with an explicit no-save close after each verified hidden scratch document.
Applying the visibility override after the first control still timed out.
These observations establish an operational difference for this build and roster. They do not identify the internal cause.

Keep the explicit visibility setting immediately before the final control.
Continue to verify an empty session and normal exit through the retained process handle.

| Private observation                       | Measurements SHA-256                                               |
| ----------------------------------------- | ------------------------------------------------------------------ |
| Original collector, normal exit           | `eb3944e58972a8a9eebdb67647783b8ca20385121e037af93b7ff25877413f39` |
| Earlier override without command batching | `5138b2d7eac4f6b281a41a6d1aef462ac4b3b8101eb5385520c296220823762f` |
| Earlier override after the first control  | `1a36cfdc5492f605c79a09cbad7dba474c78524550b01decd69688a53c471b47` |

[Final control visibility and exit evidence](../../../../Changes/Research/Workers/SolidWorks/FinalControlVisibility.md)
