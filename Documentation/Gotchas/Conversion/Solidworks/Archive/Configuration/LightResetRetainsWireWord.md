# A cleared runtime light field retains its wire word

The ordinary light serializer reads `f36c` as a signed 32-bit
word and clears that member at runtime. Keep the stored word under
`f36c#wire` and the derived zero under `f36c`. The two recorded
`f384` positions also need separate fields even when their values
agree in native saves. [Exact light evidence](../../../../../../re/solidworks/records/ConfigSceneSlice2026.md)
