from convert.formats.Fusion.GraphicsCodec.Wire.SceneState import SceneState
from convert.formats.Fusion.GraphicsCodec.Wire.ObjectValueMut import ObjectValueMut
from convert.formats.Fusion.GraphicsCodec.Wire.FinishScene import FinishScene
from convert.formats.Fusion.GraphicsCodec.Model.Values.ObjectRef import ObjectRef
from convert.formats.Fusion.GraphicsCodec.Model.State.SceneObject import SceneObject


class SceneCodec(SceneState):

    def ObjectValue(self, ClassName: str, Value: ObjectRef | None) -> ObjectRef:
        return ObjectValueMut(self, ClassName, Value)

    def LinkedObject(self, ClassName: str, Value: ObjectRef | None) -> ObjectRef | None:
        if not self.IsFlag(Value is not None):
            return None
        self.ExpectText(ClassName)
        return self.ObjectValue(ClassName, Value)

    def Finalize(self) -> tuple[SceneObject, ...]:
        return FinishScene(self)
