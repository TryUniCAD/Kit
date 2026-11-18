# Tree classes do not prove object ownership

## Expectation

A copied native node with the same class, persistent ID, field values and map index represents the same presentation owner. Removing that owner's public row together with its saved record can leave a complete smaller tree.

## Actual behavior

Archive references preserve actual object identity. A copied or independently decoded node may have equal identifiers while belonging to another graph. Existing owner checks can also validate their remaining subset without proving that every original member is still represented.

The disclosed through-all source has 21 roots, six persisted cabinet/environment children and one actual configuration helper. The new process probes reject equal-ID copied nodes and paired removal of owner records and public rows.

## Workaround

Resolve each tagged owner against the actual linked map entry and retain complete root/member/helper/public identity closure. Keep native containment, paired notes, configuration helper and unexplained-extra validation mandatory. On refusal retain public records and expose the exact failed qualification.

The [source record](../../../../../../re/solidworks/records/ThroughAllPresentationOwners2026.md) and [process receipt](../../../../../../re/solidworks/measurements/2026/ThroughAllPresentationOwners01.json) bind the evidence. Complete native presentation and source writer acceptance remain separate.
