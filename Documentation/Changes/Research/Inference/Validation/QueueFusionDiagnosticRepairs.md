# Queue Fusion diagnostic repairs

The Fusion census now pins the exact diagnostics observed on queue candidate
`8723a937571bd7e4e4780b2e7adf0cf2d5a3eb52`.
The [remote census comparison](https://github.com/TryUniCAD/Kit/actions/runs/44835681678/job/136631695007)
reported 558 changed strict-rejection messages and 16 changed rejection reasons across 714 inputs.
Every outcome, reader mode, input hash, blob identity, and qualification flag remains unchanged.
The comparator still checks complete asset records exactly and retains its malformed-input and changed-outcome controls.
The original observation identifies the initial baseline; `diagnostic_observation` records the later message-only update.

The archived P04 process now requires the exact current projection refusal.
Its integration check asserts that refusal before restoring only that diagnostic to the historical value for the existing full-report digest.
Geometry, ownership, negative controls, and the historical digest remain pinned.
See the [remote refusal failure](https://github.com/TryUniCAD/Kit/actions/runs/44835681678/job/136631695048).

These are unqualified research observations and do not establish native application acceptance.
No local tests ran; execution verification requires the next merge-group candidate.
