# SOLIDWORKS local import completed model state

The shared part constructor can publish the completed update state for a
fresh ordinary local import. It stamps the real origin and import feature
in update order, updates the active configuration's model and body state,
and synchronizes both model headers before serialization. It uses the
modeled update time and native release target.

All four previously accepted import files and their 48 logical streams
reproduced byte for byte after the update step moved into the shared part
constructor. Construction recorded zero runtime input reads. The supported
state covers one configuration and one local import body.
[Shared update comparison](../../../../re/solidworks/measurements/2026/SharedImportCompletedUpdate01.json)
[Native lifecycle evidence](../../../../re/solidworks/measurements/2026/GeneratedLocalBodyPartCompleted01.json)
