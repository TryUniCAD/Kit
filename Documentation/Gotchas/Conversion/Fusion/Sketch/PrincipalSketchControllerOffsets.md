# Sketch parameter count changes the support controller offset

A fixed offset found the support-plane controller on the paired rectangle control. It missed the same dependency on six sketches from the extrusion, revolution, scale and radius controls. Five sketches had zero parameters and two children. One had one parameter and three children.

Read the variable parameter list, sketch and matrix references, projection lists, feature label and child list. Check the matrix controller and selection descriptor in both directions and verify the selected datum's owner and frame. All six controls selected the XY datum and independently agreed with its origin and normal. [Hosted comparison](https://github.com/TryUniCAD/Kit/actions/runs/44755999849/job/136355761654)
