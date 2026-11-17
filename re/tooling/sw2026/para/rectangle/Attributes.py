from dataclasses import dataclass
from enum import IntEnum

from .Allocate import DraftNode, Ref, require


class Owner(IntEnum):
    INSTANCE = 0
    ASSEMBLY = 1
    BODY = 2
    FACE = 4
    LOOP = 5
    EDGE = 6
    GEOMETRY = 9


class Field(IntEnum):
    INT = 1
    REAL = 2
    CHAR = 3
    POINTER = 9
    UNICODE = 10


class Action(IntEnum):
    ORDINARY = 0
    PROPAGATE = 2
    PERSISTENT_ID = 5


@dataclass(frozen=True)
class Definition:
    name: str
    type_id: int
    action: Action
    owners: tuple[Owner, ...]
    fields: tuple[Field, ...]

    def nodes(self, following):
        return (
            DraftNode(self.reference, 80, {
                "next": following,
                "identifier": self.name_reference,
                "type_id": self.type_id,
                "actions": actions(self.action),
                "field_names": 0,
                "legal_owners": tuple(int(index in self.owners) for index in range(17)),
                "fields": tuple(map(int, self.fields)),
            }),
            DraftNode(self.name_reference, 79, {"string": self.name}),
        )

    @property
    def reference(self):
        return Ref("attribute-definition:" + self.name)

    @property
    def name_reference(self):
        return Ref("attribute-definition-name:" + self.name)


def actions(action):
    if action is Action.PROPAGATE:
        return (1,) * 8
    return (0, 0, 0, 0, 3, 6 if action is Action.PERSISTENT_ID else 5, 0, 0)


def sw(name, owners, fields, action=Action.ORDINARY):
    return Definition(name, 9000, owners=owners, fields=fields, action=action)


BODY = (Owner.BODY,)
FACE = (Owner.FACE,)
POINTER_INT = (Field.POINTER, Field.INT)
REAL = (Field.REAL,)
APPEARANCE = (Owner.INSTANCE, Owner.ASSEMBLY, Owner.BODY)
RECTANGLE_DEFINITIONS = (
    sw("BODY_MATCH", BODY, (Field.INT,), Action.PROPAGATE),
    sw("SWEntUnchanged", (Owner.FACE, Owner.EDGE), (Field.INT,), Action.PROPAGATE),
    sw("DOWNSTREAM_FACE_ID", FACE, (Field.INT,) * 3),
    sw("LAST_BODY_MODIFYING_FEATURE_ID", BODY, POINTER_INT),
    sw("BODY_IN_LIGHTWEIGHT_PERM", BODY, POINTER_INT),
    sw("BODY_RECIPE_2001", BODY, POINTER_INT),
    sw("ATOM_ID_2001", BODY, POINTER_INT),
    sw("ENT_TIME_STAMP_2001", BODY, POINTER_INT),
    sw("FACE_ID_2001", FACE, (Field.POINTER, Field.POINTER, Field.INT, Field.INT), Action.PERSISTENT_ID),
    sw("SWIMPLICITBODYNAME_ID_U", (Owner.BODY, Owner.FACE, Owner.LOOP, Owner.EDGE, Owner.GEOMETRY),
       (Field.UNICODE,) * 2),
    Definition("SDL/TYSA_COLOUR_2", 8040, Action.ORDINARY, APPEARANCE, REAL),
    Definition("SDL/TYSA_TRANSLUCENCY_2", 8041, Action.ORDINARY, APPEARANCE, REAL),
    Definition("SDL/TYSA_DENSITY", 8004, Action.ORDINARY, BODY, (Field.REAL, Field.CHAR)),
)
RECTANGLE_DEFINITION_BY_NAME = {definition.name: definition for definition in RECTANGLE_DEFINITIONS}


def build_definitions(names):
    require(len(names) == len(set(names)), "duplicate definitions in the registration order")
    definitions = tuple(RECTANGLE_DEFINITION_BY_NAME[name] for name in names)
    following = 0
    nodes = []
    for definition in reversed(definitions):
        nodes.extend(definition.nodes(following))
        following = definition.reference
    return following, tuple(nodes)
