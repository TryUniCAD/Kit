# The root world does not use its displayed class serializer

A world whose stored interface name is `ARenderList` appears to require the derived serializer's trailing `Accelerate` boolean. Reading that byte at the document root overruns the valid stream.

Native `PersistentObjectManager::SaveWorld` requests `IWorld::InterfaceID` for the root, while nested `ARenderList` values use their derived serializer. The root ends immediately after `WorldSerializerEndMark`; nested lists add `Accelerate`.

Select framing from the root's dispatch context as well as its stored class name. The [wire model](../../../../../re/Fusion/Reconstruction/OgsScene/WireModel.md) and [binary facts](../../../../../re/Fusion/Reconstruction/OgsScene/BinaryFacts.json) identify the native call sites and both complete controls.
