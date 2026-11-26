# SOLIDWORKS sketch dimension evidence

When several sketches save the same diameter, the dimension name and displayed value can match multiple byte offsets. The offline research command now compares the driving scalar in each owning feature with the distance between the saved center and rim, the native circle identified by its operand, the sketch constraint reference, and the strict reader’s parameter span. The report records the scalar and both geometry offsets under `verified_profile_radius`.

On the tracked turbine wheel, six previously ambiguous dimensions passed these checks. Two separate sketches contain 10.16 mm driving diameters at offsets 98288 and 114975. Thirteen dimension records remain ambiguous. The 32.73° display also matches a held-out mirror and strict reader span, reported under `verified_mirrored_dimension`. These results establish field ownership for this input. Whole-file acceptance remains open.

Run `kit run solidworks --input <part.SLDPRT> --directory <new-directory>` and inspect `Input-dimension-evidence.json`.
