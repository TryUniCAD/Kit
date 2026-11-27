# SOLIDWORKS absolute depth edits use millimetres

The research encoder's edit value is an absolute length in millimetres. An existing length may carry its own explicit unit while the surrounding document and sketch remain in millimetres. Replacing only the numeric value would turn a 19.87 mm edit of a metre-valued source into a 19.87 m extrusion.

Replace the number and its unit together and bind the same typed value to D1 and the extrusion length. Evaluate a no-op after converting both valid plans to native metres. For example, 0.0125 m and 12.5 mm give the same binary64 native value. [Offline edit replay](../../../Changes/Research/Encoder/SolidworksAbsoluteDepthUnits.md)
