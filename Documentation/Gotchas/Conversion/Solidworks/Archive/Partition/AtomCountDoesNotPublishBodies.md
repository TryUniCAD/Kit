# An atom count does not publish live bodies

An archive's atom map can contain an actual `moAtom_c` while that atom's runtime body pointer remains null. The pinned 2026 loader creates the atom indexes and manager aliases independently from later body publication. Ordinary `body_kind=0` explicitly starts with runtime `atom+0x160` null.

The actual `moAtomManager_c::getBodies` can return through a selected runtime cache before normal iteration. Its normal path then applies atom-state, feature, body-pointer, body-type, validity and identity checks. Counting atom rows, a configuration saved-body word, or kernel partition bodies therefore cannot substitute for the returned public body inventory.

Inspect the reached body-query path and retain actual manager/atom/body aliases plus output count. Do not change the saved body discriminator or fill a runtime pointer from an observed native handle. Observe the application's existing atom-ID getter calls because that getter can repair a runtime pointer mirror.

The [source record](../../../../../../re/solidworks/records/AtomManagerBodyEnumeration2026.md) binds the exact ordinary branch, current-version reload owner, original hashes and bounded observation apertures. It does not establish native acceptance for a generated part.
