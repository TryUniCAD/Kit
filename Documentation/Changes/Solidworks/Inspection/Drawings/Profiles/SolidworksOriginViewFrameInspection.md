# Inspect drawing placement after a linked child edit

The ordinary COM origin lifecycle observer now projects an edited child through the existing constructed model-to-view frame. It computes the child's edited center of mass separately. Only a declared view move translates the drawing frame.

The first trial opened and saved Alpha, then reopened it in a fresh process. Its subsequent child-width edit rebuilt and saved cleanly. The drawing's initial outline grew on the positive X side while its entire placement transform stayed equal to the prior saved drawing. The old observer instead recentered its prediction around the new body bounds. It failed before the drawing rebuild or view move. This failed trial remains failed.

The corrected packet keeps all generated input bytes, complete trees, actual relation identities, analytic body measures, full transforms, outlines, exact paths, configurations, numeric tolerances, fresh-process phases and controls. It records each complete actual and predicted drawing state before comparison. Preservation through rebuild, move, save and reopen remains an explicit hypothesis for the new trial to measure.

The private packet uses the existing `InspectSdkOriginLifecycle.py verify`, `preflight` and `run` commands with a new packet hash. Verification starts no CAD process. Preflight still requires every exact working destination to be absent. The root-owned oracle operator must preserve the earlier task-owned files and their measured hashes before restaging identical generated inputs.

The corrected disclosed trial passes eighteen fresh native processes with both controls healthy. Its sixteen candidate phases pass 3,328 numeric comparisons. Each pair retains its twenty-five child rows and sixteen drawing rows through a size edit, view move, save and fresh reopen.

Two independent host reader processes verify all eight saved drawing/child states. Complete Definition bytes, maps, aliases, actual origin IDs, creation epochs, file paths and selected configurations match.

This qualifies the four generated disclosed lifecycles only. Original source conversion, held-out acceptance, pixel-level glyph rendering and public drawing writing remain outside this result. See [the measured receipt](../../../../../../re/solidworks/measurements/2026/SdkOriginDrawingDisclosedNative01.json) and [the scoped record](../../../../../../re/solidworks/records/SdkOriginDrawingDisclosedNative2026.md).

See [the view-frame gotcha](../../../../../Gotchas/Conversion/Solidworks/Drawings/Qualification/ChildEditsDoNotProveViewRecentering.md).
