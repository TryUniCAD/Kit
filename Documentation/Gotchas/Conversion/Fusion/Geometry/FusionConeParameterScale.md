# Fusion cone parameter scale is not the upper radius

An ASM `cone-surface` stores an ellipse followed by sine, cosine, a dimensional parameter scale, sense and optional parameter limits. Interpreting the third scalar as the top radius appears plausible for a cylinder because the values coincide, but produces the wrong parameterization for a taper.

Native `cone::eval` uses the first surface parameter for longitudinal motion and the second for the angular direction. For a circular forward cone with positive cosine, axial motion is `u * scale * cosine` and radial growth is `u * scale * sine`. Thus the geometric radius at height `z` is `baseRadius + z * sine / cosine`. The upper radius is determined by the trimming topology and height, not a second radius field on the surface record.

The independent writer chooses the native-compatible scale `baseRadius`, computes signed sine and positive cosine from the requested radius difference and height, and generates the two circular boundary carriers separately. In SMB, both the major vector and scale are dimensional and convert from millimetres to centimetres; sine and cosine do not scale. SMT keeps millimetres.

The controlled 7-degree taper source stores base radius 1 cm, scale 1 cm and upper rim radius 1.2087337535349378 cm at height 1.7 cm. Exact source hashes, native symbols and field-level evidence are in [ConeEvidence.json](../../../../../re/Fusion/Reconstruction/FrustumModel/ConeEvidence.json), with the [equations and topology](../../../../../re/Fusion/Reconstruction/FrustumModel/FrustumModel.md). The installed kernel's save/restore version constants use an internal version scheme and should not be substituted for the outer file-format header.
