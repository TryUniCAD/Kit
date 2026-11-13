from convert.formats.Fusion.GraphicsCodec.Wire.SceneState import SceneState
from convert.formats.Fusion.GraphicsCodec.Wire.ObjectValueMut import ObjectValueMut
from convert.formats.Fusion.GraphicsCodec.Wire.FinishScene import FinishScene
from convert.formats.Fusion.GraphicsCodec.Model.Values.ObjectRef import ObjectRef
from convert.formats.Fusion.GraphicsCodec.Model.State.SceneObject import SceneObject
from convert.formats.Fusion.GraphicsCodec.Fields.XferOverrideMut import XferOverrideMut
from convert.formats.Fusion.GraphicsCodec.Model.Values.OverrideSet import OverrideSet


class SceneCodec(SceneState):

    def ObjectValue(self, ClassName: str, Value: ObjectRef | None) -> ObjectRef:
        return ObjectValueMut(self, ClassName, Value)

    def LinkedObject(self, ClassName: str, Value: ObjectRef | None) -> ObjectRef | None:
        if not self.IsFlag(Value is not None):
            return None
        self.ExpectText(ClassName)
        return self.ObjectValue(ClassName, Value)

    def OverrideSets(
        self, Values: tuple[OverrideSet, ...] | None
    ) -> tuple[OverrideSet, ...]:
        return XferOverrideMut(self, Values)

    def Finalize(self) -> tuple[SceneObject, ...]:
        return FinishScene(self)
