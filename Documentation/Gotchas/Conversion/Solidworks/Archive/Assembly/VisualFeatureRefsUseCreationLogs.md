# Visual feature references use creation logs

A feature reference in `VisualStates` carries its creation seconds
from the feature's first actual log event. The resolved feature's
FILETIME words can record a different instant. All 30 disclosed child
references match both native header logs while their FILETIME differs.
In the measured parent cases the two values happen to agree.

For new graphs, join the actual feature ID to matching events in
Config-0-ModelHeader and Header2. When both logs are empty for the
feature, use the documented unset-time value of 2592000. Refuse
divergent header ownership. In two fresh model compositions, changing
only FILETIME changes ResolvedFeatures and preserves VisualStates
byte for byte.

[Creation-time getter](../../../../../../re/solidworks/records/ModelConstruction2026.md#feature-reference-creation-time)
· [Observed contrast](../../../../../../re/solidworks/measurements/2026/ConcentricVisualCreationLogs01.json)
