# Native radial dimensions use the radius input spelling

An independent native source specification can describe a circle dimension as `radial`. The neutral circle constructor accepts `radius` or `diameter`; passing `radial` directly raises `ConstructionError` before the complete part can be serialized.

Normalize `radial` to `radius` in the evaluation adapter before calling the frozen neutral-input adapter. Keep the original public source specification unchanged, retain the same numerical radius, and do not alter the frozen writer or inspect sealed native observations to diagnose this vocabulary mismatch.

The first camera prediction run at `cbb72d01e32a915376c80744a9ab0cba90c82a8b` exposed this failure in [the native-format CI job](https://github.com/TryUniCAD/Kit/actions/runs/43952979781/job/133600109341). The repair is recorded in [the camera prediction entry](../../../../../Changes/Solidworks/Inspection/Presentation/SolidworksCameraHeldoutPrediction.md). This is an evaluation-input issue, not evidence of native loadability.
