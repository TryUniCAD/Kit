# Appearance presence does not mean populated data

The drawing UI material-presence byte describes a nonnull `PWMaterialManager_c` pointer. It does not count appearances. The native document constructor allocates that manager even while its saved reference collection is empty, so treating every nonzero presence byte as populated material data rejects otherwise understood state.

The two exact disclosed sources each contain presence one, an allocator value of one, and zero declared and actual reference rows. That observed allocator value is separate from the native constructor seed and cannot replace arbitrary saved allocation history.

Read the two signed32 wire halves as one unsigned64 counter and retain them on the graph. Admit only a genuinely empty, consistent collection until populated appearance projection is implemented. Reject null rows and inconsistent counts as well as ordinary populated entries. Do not remove the presence byte, discard a manager, reset the counter, or widen unrelated root/link checks to obtain a passing read.

The [native ownership record](../../../../../../../re/solidworks/records/DrawingEmptyAppearanceAdmission2026.md) and [independent process receipt](../../../../../../../re/solidworks/measurements/2026/DrawingEmptyAppearanceReader01.json) bind four counter-persistence cases, fifteen expected rejections, all 43 prior workers, and both retained original failures.
