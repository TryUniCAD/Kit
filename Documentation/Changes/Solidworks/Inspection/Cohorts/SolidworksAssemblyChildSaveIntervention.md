# Compare parent saves with and without an explicit child save

The [assembly discovery reader](../../../../../re/solidworks/measurements/2026/AssemblyStampProcesses34a.json)
found that the saved reference timestamp follows the parent header timestamp
in the two populated inputs. The [native probe](../../../../../re/solidworks/measurements/2026/AssemblyReferenceProbe03.json)
also found the rebuild requirement on the parent, while the loaded child
reported no rebuild required after open.

The new discovery intervention starts from identical isolated copies of the
same control part. Both new assemblies contain one ordinary occurrence and
mark their child copy dirty. One saves only the parent. The other calls
[native `Save3`](https://help.solidworks.com/2026/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IModelDoc2~Save3.html)
on its exact owned child before saving the parent. The probe records the
child's update stamp, actual disk hashes, geometry, load status and active
configuration in six fresh processes including two controls.

The procedure checks the ownership of the saved child path and never writes
the original control. The [completed six-process receipt](../../../../../re/solidworks/measurements/2026/AssemblyChildSaveProbe01.json)
records healthy controls and matching geometry. The parent-only case returned
warning 32 and reopened the child at stamp 120. An explicit child save kept
stamp 134 and both the load warning and parent rebuild flag were zero. This
is a diagnostic using private native copies; it adds no writer acceptance.
