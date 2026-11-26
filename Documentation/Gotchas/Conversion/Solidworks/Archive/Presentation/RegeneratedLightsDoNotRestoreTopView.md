# A native resave can leave the top annotation view missing

SOLIDWORKS 2026 SP04.1 saved a Kit-authored blind boss with the same four measured lights as an independently authored boss of the same geometry. Fresh read-only open and rebuild exposed two annotation views in the vendor part and one in the saved Kit part. The missing view was the vendor's hidden, assigned view. Its native rotation matched all nine entries of the `*Top` annotation transform decoded from `Contents/Config-0`.

For source fidelity, compare the actual annotation roster, rotation and state against a native control. Correlate each assigned view with the decoded configuration record. The native light roster and a clean rebuild can both match while an assigned annotation view remains missing.

[Native contrast evidence](../../../../../../re/solidworks/measurements/2026/VendorBossCorpus/PresentationContrast.json)
