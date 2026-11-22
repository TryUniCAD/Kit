# Fusion extent station keys

Converting an extrusion lower station and height to centimeters separately can produce a different floating point result from adding them in millimeters before conversion. With lower -8 mm and height 23 mm, the two expressions give 1.4999999999999998 and 1.5. Native geometry agrees within the documented tolerance, but exact label coverage keys can differ.

Use the same canonical arithmetic for the label reader and coverage collector. Keep exact coverage identity checks on the resulting keys and tolerant comparisons against native coordinates.

The API-authored 15 mm along and 8 mm against control is recorded in `re/Fusion/Reconstruction/CircularSpans/Controls/Rounding` and its independent measurements are in Manifest.json. It is included in the process boundary CLI replay; local tests were not executed.
