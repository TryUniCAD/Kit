# SOLIDWORKS drawing profile-display retention

The typed ordinary 2026 Definition reader/store now retains understood profile-display references in a view-owned detail folder. `NamedRead.ProfileDisplays` and `FrontRead.ProfileDisplays` expose actual display, folder, view and component-profile objects plus the native suppression flag. Nonempty collections add `drawing.profile_displays` to `Unprojected`.

The rule requires exact current descriptors and actual owner aliases. It accepts only the known flag bit and empty auxiliary integer sets, links and optional state. Other 33 detail-folder collections and annotation buckets remain guarded. No class layout, constructor, public adapter registration or saved default is added.

Root's exact 4,389-source replay passed all 43 prior workers, both complete original normal Definition byte/map/identity comparisons, 86 malformed full-store cases and four complete authored-flag variants. The unchanged generated Front control remains exact. The public adapter still limits `strict=False` to layout inspection and rejects `strict=True`; portable child-sketch resolution, original writer equivalence and native/held-out conversion acceptance remain unqualified.

See the [native field ledger](../../../../../../re/solidworks/records/DrawingProfileDisplayRetention2026.md), [sanitized receipt](../../../../../../re/solidworks/measurements/2026/DrawingProfileDisplayRead01.json) and [shared-folder gotcha](../../../../../Gotchas/Conversion/Solidworks/Drawings/Qualification/ProfileDisplaysShareDetailFoldersWithAnnotations.md).
