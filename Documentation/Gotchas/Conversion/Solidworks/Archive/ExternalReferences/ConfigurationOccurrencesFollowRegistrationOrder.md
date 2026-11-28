# Configuration occurrences follow registration order

An ordinary assembly saves its references in feature order. The active configuration keeps a separate list of component state records in first-registration order. When SOLIDWORKS 2026 first activates a configuration after inserting its features, it scans the unified feature array backward to register missing occurrence paths. Serial insertion can register each path as the occurrence is added.

Keep the existing componentless configuration row. To model activation after feature construction, walk new references in reverse feature order and append one row per path. The A14 discovery assembly stores reference ids 24 and 25 in Config-0 and stores the componentless row followed by 25 and 24 in CMgr. [Native registration trace and readback](../../../../../../re/solidworks/records/OrdinaryOccurrenceConstruction2026.md#configuration-registration-and-shared-file-identity)
