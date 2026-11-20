# The local width clone uses a driver ordinal

The width and height annotation handles in the disclosed rectangle
share the same sketch owner. The width operand's cloned handle must
also select the actual width ordinal. Matching the relation text,
sketch owner and cached value can still admit a clone that points to
height. The clone needs its own local unit component with the same
part root.

Match the complete cloned selection to the live width handle. The
SDK proof moves the clone to the actual height ordinal, updates its
cached value and observes rejection. Removing its unit component
also withholds the typed dependency.

[Handle and owner measurements](../../../../../../re/solidworks/measurements/2026/SdkLocalWidthDepthRead01.json)
