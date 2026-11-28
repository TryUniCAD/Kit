from dataclasses import dataclass
from uuid import UUID

from ExchangeMessagePack import ExchangeMap, encode_config_atom, read_exchange_map
from convert.adapters.solidworks.Archive.CmgrHeader.ManagerSchemas import KConfigHdrClass
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import ReadStyleText
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt, ReadNodeName, ReadRows, RequireRecord


CONFIG_HEADER_STREAM = "Contents/3DExperienceExchange_ConfigHeader"
MODEL_EXCHANGE_STREAM = "Contents/3DExperienceExchange2"
CONFIG_FIELDS = ("_3dExpType", "class", "configHeaderfamilyMemberID", "id", "name", "repParent")


@dataclass(frozen=True, slots=True)
class ConfigHeaderExchange:
    configuration_id: int
    name: str

    def __post_init__(self):
        if (type(self.configuration_id) is not int or not 0 <= self.configuration_id < 1 << 31
            or type(self.name) is not str or not self.name
            or not ReadStyleText(self.name, "configuration exchange name")):
            raise ValueError("ordinary exchange needs an explicit configuration identity and name")


def check_class(node, kind):
    if not isinstance(node, ArchiveNode) or node.ClassValue != kind:
        raise ValueError("exchange requires actual " + kind.NameValue)


def project_config_header(lightweight, configuration):
    check_class(lightweight, KConfigHdrClass)
    check_class(configuration, RuntimeClass("moConfiguration_c", 1))
    fields = lightweight.FieldsValue
    authored = ConfigHeaderExchange(FieldInt(configuration.FieldsValue, "f08"), ReadNodeName(configuration))
    if (FieldInt(fields, "f08") != 1 or FieldInt(fields, "f34") != -1
        or FieldInt(fields, "f30") != authored.configuration_id or fields.get("f10") != authored.name
        or fields.get("f60", -2) != -2 or fields.get("f68", "") != ""):
        raise ValueError("lightweight header does not own the ordinary active exchange configuration")
    return authored


def encode_config_header(model):
    if type(model) is not ConfigHeaderExchange:
        raise ValueError("configuration header exchange requires an ordinary typed model")
    values = (0, KConfigHdrClass.NameValue, -2, model.configuration_id, model.name, "")
    return bytes((0x80 + len(CONFIG_FIELDS),)) + b"".join(
        encode_config_atom(name) + encode_config_atom(value)
        for name, value in zip(CONFIG_FIELDS, values, strict=True)
    )


def read_uuid_key(key):
    if type(key) is not bytes:
        raise ValueError("exchange requires a canonical version-four UUID key")
    try:
        text = key.decode("ascii")
        identity = UUID(text)
    except (UnicodeError, ValueError):
        raise ValueError("exchange requires a canonical version-four UUID key") from None
    if len(key) != 36 or identity.version != 4 or str(identity) != text:
        raise ValueError("exchange requires a canonical version-four UUID key")
    return identity


def config_header_cell(model, record_id):
    if type(record_id) is not UUID or record_id.version != 4:
        raise ValueError("configuration exchange needs its separately allocated version-four UUID")
    return str(record_id).encode("ascii"), encode_config_header(model)


def read_config_header(key, payload):
    identity = read_uuid_key(key)
    fields = read_exchange_map(payload)
    if tuple(name for name, _ in fields.pairs) != CONFIG_FIELDS:
        raise ValueError("configuration header has unqualified exchange fields or order")
    if (type(fields.field("_3dExpType")) is not int or fields.field("_3dExpType") != 0
        or fields.field("class") != KConfigHdrClass.NameValue
        or fields.field("configHeaderfamilyMemberID") != -2 or fields.field("repParent") != ""):
        raise ValueError("configuration header has a family or representation exchange owner")
    model = ConfigHeaderExchange(fields.field("id"), fields.field("name"))
    if encode_config_header(model) != payload:
        raise ValueError("configuration header has a noncanonical MessagePack encoding")
    return model, identity


def project_active_config(manager):
    check_class(manager, RuntimeClass("moConfigurationMgr_c", 1))
    fields = manager.FieldsValue
    list_fields = RequireRecord(fields.get("f370"))
    rows = ReadRows(list_fields.get("items"))
    active = fields.get("f360")
    if (len(rows) != 1 or FieldInt(list_fields, "n") != 1
        or rows[0].get("o") is not active or fields.get("f368") is not active):
        raise ValueError("exchange requires one actual active manager configuration")
    check_class(active, RuntimeClass("moConfiguration_c", 1))
    return active


def read_model_exchange_link(records, manager, model):
    active = project_active_config(manager)
    selected = ConfigHeaderExchange(FieldInt(active.FieldsValue, "f08"), ReadNodeName(active))
    if type(model) is not ConfigHeaderExchange or model != selected:
        raise ValueError("configuration header is detached from the active model configuration")
    maps = {key: read_exchange_map(value) for key, value in records}
    if len(maps) != len(records) or b"TOC" not in maps:
        raise ValueError("model exchange lacks its unique TOC")
    toc = maps[b"TOC"]
    nested = toc.field("model")
    if (toc.field("class") != "object-map" or type(nested) is not ExchangeMap
        or nested.field("class") != "moAssembly_c"
        or type(nested.field("configid")) is not int or nested.field("configid") != model.configuration_id
        or nested.field("configname") != model.name):
        raise ValueError("model exchange TOC selects a different assembly configuration")
    managers = tuple((key, value) for key, value in maps.items() if "moConfigurationMgr_c" in value.values("class"))
    if len(managers) != 1:
        raise ValueError("model exchange requires a unique configuration manager record")
    key, config_manager = managers[0]
    if config_manager.values("class") != ("moConfigurationMgr_c",):
        raise ValueError("model exchange configuration manager has conflicting class ownership")
    if type(config_manager.field("id")) is not int or config_manager.field("id") != FieldInt(manager.FieldsValue, "f08"):
        raise ValueError("model exchange manager has a foreign persistent node identity")
    if config_manager.field("overriddenReferenceIDs") != ():
        raise ValueError("ordinary configuration exchange refuses nonempty persisted reference overrides")
    return read_uuid_key(key), ()
