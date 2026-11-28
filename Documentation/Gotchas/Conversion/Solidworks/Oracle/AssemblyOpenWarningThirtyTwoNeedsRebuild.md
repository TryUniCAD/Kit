# Assembly open warning 32 means the document needs a rebuild

Fresh loads of the one- and two-occurrence native discovery assemblies
returned zero errors and warning `32`; loading the empty assembly returned
zero warnings. All were created by the pinned 2026 oracle. The
[2026 warning enumeration](https://help.solidworks.com/2026/English/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swFileLoadWarning_e.html?id=3b36a39206d34f468a0d2c24bef11595)
identifies this bit as `swFileLoadWarning_NeedsRegen`. It is separate from the
read-only or view-only warnings.

Record the warning before any rebuild. A successful explicit rebuild or a
passing volume comparison cannot erase it from the original open result.
Use a separate saved copy to measure whether the rebuild state persists,
keeping the original candidate and referenced part immutable.

The [second source attempt](../../../../../re/solidworks/measurements/2026/AssemblySourceAttempt02.json)
remains failed and ineligible for held-out use.
