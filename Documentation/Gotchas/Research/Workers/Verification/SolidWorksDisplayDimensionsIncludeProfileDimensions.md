# SOLIDWORKS display dimensions include profile dimensions

`GetFirstDisplayDimension` can return dimensions inherited from a feature's profile.
It does not establish that the feature owns every returned dimension.
The recorded P03 boss observations include profile width and height as well as the boss depth.

Counting all display dimensions as extrusion controls creates duplicate parameters and ambiguous length bindings.
The native verifier first checks the owner component of `IDimension.FullName`.
It then checks `GetFeatureOwner` against the feature with the application object's identity API before assigning semantic ownership.
The edit batch selects only the resulting independent driving parameters.

The independently authored capture is recorded under [P03 SOLIDWORKS observations](../../../../../re/automation/PairedCaptures/P03/solidworks-db1390476325/measurements.json).
No licensed SOLIDWORKS execution was available during implementation.
