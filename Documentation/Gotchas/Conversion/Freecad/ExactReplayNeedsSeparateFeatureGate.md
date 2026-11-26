<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Exact replay needs a separate fresh-output feature gate

An unchanged native file can be preserved even when its observed graph is too incomplete to reconstruct. Running the fresh editable-output gate before source-bound exact replay incorrectly refused all 23 source-authored FreeCAD alias controls. Their parser observations had no base sketch; their successful reads did not imply usable native geometry.

Preserve the source only after checking the retained archive payload, its companion SHA-256 binding, the recorded model digest and a fresh native reparse. Then run the existing feature gate. For unsupported reconstruction features on this proven replay path, preserve exact bytes only with false loadability/usability flags, carrier/source-opaque transfers and an explicit diagnostic. Do not turn byte equality into evidence of native editability.

A changed parameter, mismatched payload or binding, or a requested rebuild still requires the normal refusing gate. Strict public output must leave existing stream or file bytes untouched. Unsupported fresh writing must not inherit the replay exception.

The [repair and process evidence](../../../Changes/Freecad/FreeCadExactReplayOrdering.md) record the bounded A16f/A16g behavior. Actual FreeCAD geometry, edit, save and fresh-reopen witnesses retain their separate source and artifact pins.
