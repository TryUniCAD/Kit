# A selected revolve face can omit its cache words

A saved `moCompSolidBody_c` can contain a live `ff0` face even when `f100` and `f104` are both zero. The Top-plane reversed outer-stock case retained this pair on its original save and after a D1 edit. The other three authored models kept `58` and the actual result atom. All four kept `f108 = -1` and the actual consumed stock atom.

Use the live face, the selected producer, both chooser arrays and the validated result partition to establish the body's identity. Only the fully empty pair or the corroborated populated pair is supported. [Source lock](../../../../../../re/solidworks/measurements/2026/SdkAuthoredRevolveFaceSourceLock01.json) · [Readback and refusal checks](../../../../../../re/solidworks/measurements/2026/SdkAuthoredRevolveFaceCache01.json)
