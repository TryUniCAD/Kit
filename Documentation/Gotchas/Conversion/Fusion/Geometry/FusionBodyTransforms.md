# Fusion body transforms have their own field and unit roles

Most topology records begin with an attribute reference, an entity tag and a reserved reference. A transform does not have that third field. Its first basis vector immediately follows the entity tag. Applying the common topology prefix shifts every transform field and corrupts the stream.

The three vectors are basis columns. They are not rows, vertex coordinates or normalized directions that can be rescaled independently. A fourth vector is translation in centimetres, followed by a separate scale factor and the rotation, reflection and shear flags. Native position evaluation multiplies the three-column matrix by the point, applies the scalar, then adds translation. Scaling the translation as well produces the wrong placement.

The full indexed inventory contains many explicit transform records that all encode identity. That observation proves their framing but cannot alone establish a nonidentity convention. Native serializer, restorer and position-operator instructions supply the missing evidence. Classification flags remain explicit fields rather than inferred convenience values.

Use the named `TransformNode` values, preserve them during serialization, and apply the proven matrix/scale/translation order when interpreting geometry. The planar view uses the linear determinant for volume and orientation, rejects singular placement, and keeps kernel unit metadata separate from coordinate lengths.

[Static native evidence](../../../../../re/Fusion/Reconstruction/PlanarTopology/TransformEvidence.json) includes exact instruction ranges, literal flag names and binary digests. The [feature entry](../../../../Changes/Fusion/Geometry/FusionPolyhedra.md) defines the qualified geometry and acceptance boundary.
