# Successive reader passes

For a SOLIDWORKS part with a strict decode, `kit run solidworks --input <part> --directory <new-directory>` now runs field and count discovery against its latest verified reader. Each accepted change takes effect in a private source copy. A fresh process decodes the same part, compares the new evidence and tries the next rule. Every previously verified parameter must retain its value, type and provenance. The run accepts at most eight passes.

`Reader.patch` contains the cumulative source diff against the recorded base commit. `Input-reader-passes.json` records the affected parameter IDs and stop reason. `Input-candidate-dimension-evidence.json` contains evidence from the accepted reader. The original strict decode remains available for comparison.

In a detached checkout with the previously published mirrored-field and count tables held back, the turbine wheel yielded its precise angle on pass one and both circular pattern counts on pass two. Applying the cumulative patch and decoding the part again produced byte-identical strict JSON to the final candidate. This verifies recovery of known fields. Unsupported fields still require other experiments.
