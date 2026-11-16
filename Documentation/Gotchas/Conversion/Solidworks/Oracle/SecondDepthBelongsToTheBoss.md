# The second extrusion depth belongs to the boss

Expectation: refreshing qualified dimension names retains the actual owning feature for every declared driving-dimension role.

Actual behavior: the first [end-condition source attempt](../../../../../re/solidworks/measurements/2026/EndConditionAttempt01.json) created the two-direction feature and read its second depth successfully, then the harness rejected native `D2@CurveBoss@Part1.Part`. The older owner lookup recognized only the role `depth` as a boss dimension and incorrectly classified `reverse-depth` as a sketch dimension. This was a harness rejection; it does not establish a vendor geometry or file-format failure. Both independent controls passed before and after, and the incomplete family produced no lock.

Workaround: recognize both declared extrusion-depth roles as boss-owned, recognize only indexed curve roles as sketch-owned and reject unknown roles. Continue checking the returned feature name and preserve the exact native parameter identities. Restart a complete controlled family in a new output directory; earlier passing cases do not replace the required complete lock.
