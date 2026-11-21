# Binary Parasolid import needs preference readback

For the ordinary Parasolid translator, read the current 3D Interconnect
setting through `GetUserPreferenceToggle`. Setting it off with
`SetUserPreferenceToggle` produced a falsy return in the first two
native-export controls. The control observer stopped before importing.
[Initial control receipt](../../../../../../re/solidworks/measurements/2026/LocalKernelExchangePreference01.json)

Read the actual enabled value after the setter, then restore and verify
the original value when the phase ends. With this observer correction,
both native export controls and all three input bodies passed.
[Corrected exchange receipt](../../../../../../re/solidworks/measurements/2026/GeneratedLocalKernelExchangeNative01.json)
