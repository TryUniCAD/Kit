# SOLIDWORKS 2026 centered rectangle construction

A centered, two-length Front Plane rectangle creates two construction diagonals between opposite corners of its ordinary extruded contour. The two diagonals share a local center through point-on-line coincidences. A third coincidence joins that center to the component sketch handle for the part's actual Origin. The whole candidate uses the same body, dimension and origin-reference constructors as the corner profile. [Shared builder](../../tooling/sw2026/builders/RectangleAnchor.py)

## Native graph and constructor fields

The original, width-edited and height-edited disclosed native files have seven wire line entries and six COM-visible segments. Four are ordinary edges and two are construction diagonals. The extra wire entry has the nonpermanent low flag and no allocated line index. It goes from the center to one vertex. None of the three type-9 relations selects that entry. The three linked archive snapshots have audit digest `aaa5b24a47c45268b0c5cb1f515cc1f1e52bdd401a328cd063a8cd9ead73caa9`. [Native source controls](RectangleAnchorSources2026.md)

| Owner | Classification | Construction |
| --- | --- | --- |
| Four contour points and body | Input and derived | Use the authored symmetric rectangle and existing ordinary blind extrusion rules. Bind the four-edge contour before adding the reference geometry. |
| Local center and external origin point | Derived | Both are local zero in the Front Plane. The center has the ordinary type-1 point marker and gets the next local point ID. The selected external point uses the document's existing origin handle and the following point ID. |
| Two diagonal lines | Derived | Link each existing opposite point pair and set the ordinary construction bit. Allocate the next two line IDs and exclude both from the body contour. |
| Endpoint ownership | Derived | Count the three incident visible segments at every corner. Preserve the original two boundary handles used by the ordinary contour. The center has zero endpoint incidences. |
| Three type-9 relations | Derived and constant | One actual point/line handle pair per diagonal and one point/point origin join. Use the same two-handle constructor flags and sentinel fields as the corner. The center has three relation references, and each diagonal has one. |
| Line and point counters | Derived | Advance the local point and line IDs by the generated ownership. Preserve the ordinary boundary frontier and compute the fresh line-array counter from its own rows. |
| Auxiliary center-to-corner line | Volatile | The fresh generated candidate omits this unreferenced source entry. Native edit/save/reopen and both typed saved audits qualify the omission for this disclosed profile. |

## Guarded and native results

Two fresh processes emitted the same 8,440 bytes with three type-9 relations, a real shared Config/Resolved map and zero runtime input reads. The unanchored and corner profiles reproduce their earlier bytes. An off-origin centered request is rejected. All eight non-XML streams in each construction round-trip.

The generated model retains the same 25 feature rows, six visible edges, two construction diagonals and nine relations in its original, independent width edit, independent height edit and both fresh reopen states. All 205 numeric comparisons pass. Both clean saves retain six wire line entries and the actual origin link. Fourteen saved-stream round trips pass byte for byte. Both pristine controls pass across six distinct processes.

The first original centered held-out remains sealed. The evidence covers one disclosed case and its independent edits. [Native construction receipt](../measurements/2026/GeneratedCenteredRectangleNative01.json)
