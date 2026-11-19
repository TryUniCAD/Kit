from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from downstream.Components import write_component_body


StorageIdentifier = int | tuple[int, int]


@dataclass(frozen=True)
class ConfigurationCache:
    storage_id: StorageIdentifier
    opened_model: bool
    needs_rebuild: bool
    is_current: bool
    cache: ArchiveNode | None
    cache_needs_update: bool


def decimal_word(value: int) -> str:
    if type(value) is not int or not -0x80000000 <= value <= 0x7fffffff:
        raise ValueError("configuration storage identifier requires a signed i32")
    return str(value)


def configuration_storage_name(storage_id: StorageIdentifier) -> str:
    if type(storage_id) is tuple:
        first, second = storage_id
        return f"FlexCfg-{decimal_word(first)}-{decimal_word(second)}"
    return f"Config-{decimal_word(storage_id)}"


def cache_path(storage_id: StorageIdentifier) -> str:
    return f"Contents/{configuration_storage_name(storage_id)}-DownstreamIdData"


def store_part_caches(
    generated_streams: Mapping[str, bytes], configurations: Iterable[ConfigurationCache],
) -> dict[str, bytes]:
    result = dict(generated_streams)
    seen = set()
    for state in configurations:
        stream = cache_path(state.storage_id)
        if stream in seen:
            raise ValueError("part cache save repeats the configuration storage name")
        seen.add(stream)
        if (state.needs_rebuild and not state.is_current) or not state.opened_model:
            continue
        if state.cache is None or state.cache_needs_update:
            result.pop(stream, None)
            continue
        result[stream] = write_component_body(state.cache)[0]
    return result
