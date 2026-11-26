# The second SOLIDWORKS phase includes authoring

A second-phase duration can appear to measure file verification alone.
The phase also changes driving dimensions, saves edited parts, restores parameters and creates variants.
Its duration cannot determine the required builder-to-verifier instance ratio.

Use the separate per-case timing stages to distinguish authoring from saved-file verification.
The `baseline_reopen` stage includes its unchanged rebuild and repeat save.
The `edit_generation` and `variant_generation` stages measure their creation and save work.
The `saved_file_verification` stage measures reopening, rebuilding, measurement, closure and hash checks for the complete saved roster.
Startup and healthy controls have separate records.
Open retry delays remain inside the operation that needed them.

See [retry and timing behavior](../../../../Changes/Research/Supervisor/Catalogue/SolidWorksOpenRetriesAndTiming.md).
