# Read selected revolve faces with empty cache words

SOLIDWORKS 2026 can retain the live source face and its consumed-body reference while leaving both saved cache words empty. The strict reader validates that face, the archive aliases, the actual stock owner and the resulting partition in this state. A partially populated pair or a mismatched owner still fails validation.

Eight immutable saves across four independently authored models projected correctly and replayed 16 linked streams exactly. Four ownership mutations on the empty-pair case were refused. [Disclosed evidence](../../../../../re/solidworks/measurements/2026/SdkAuthoredRevolveFaceCache01.json)
