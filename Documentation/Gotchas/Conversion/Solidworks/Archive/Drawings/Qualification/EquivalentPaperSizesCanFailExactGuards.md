# Equivalent paper sizes can fail exact guards

The frozen ANSI A constructor compares the neutral width and height with `11 * 0.0254` and `8.5 * 0.0254` using exact floating equality. A source layout decoded as height `0.2159` m is one binary64 ulp above the latter expression. Both first partial geometry workers therefore rejected the paper before producing files.

Keep that rejected attempt. For an explicitly declared ANSI A input, compute both dimensions from the documented inch-to-metre formula and disclose the canonicalization. Do not change the frozen writer after held-out exposure, silently widen admission, or present this input normalization as a new native result.

[Retained failed and corrected request evidence](../../../../../../../re/solidworks/records/SdkOriginalDrawingAdmission2026.md).
