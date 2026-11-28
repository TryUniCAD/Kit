# Radial driver ownership follows the profile feature

An authored fresh neutral circle can attach its radial parameter to the portable sketch id. The ordinary native reader retains a separate profile feature and sketch. Its parameter owner is the actual profile feature, not the sketch id.

Checking only equality with sketch.id therefore rejects a correct public read. Follow parameter.owner_id to the actual feature, require that feature's sketch_id to equal the sketch id, and require the parameter id in both owners' parameter collections. Keep radial mode, driving role and numerical value checks.

Core/Adapter.Parameters explicitly projects owner_id=FeatureId(Feature.object_id). The exact public integration read follows that feature-to-sketch-to-driver chain. No reader identity was invented or changed to satisfy a test.

[Integration record](../../../../../re/solidworks/records/SdkCirclePublicRegistration2026.md) and [public parameter projection](../../../../../src/convert/adapters/solidworks/Core/Adapter.py) document the ownership. The retained initial assertion failure is separate from native acceptance.
