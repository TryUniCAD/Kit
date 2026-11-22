from collections.abc import Mapping, Sequence
from re import compile as CompileRegex

from convert.adapters.solidworks.Container.Format import KitResolvedStream
from convert.adapters.solidworks.Core.Native import NativeConfig

# native configuration lanes carry their ids in physical resolved stream names
KResolvedConfigStream = CompileRegex(r"^Contents/Config-(\d+)-ResolvedFeatures$")


# both dispatch and ordinary reads need the same physical configuration lanes
def ResolvedLanes(Streams: Mapping[str, bytes]) -> dict[int, str]:
    return {
        int(Match.group(1)): NameValue
        for NameValue in Streams
        if (Match := KResolvedConfigStream.fullmatch(NameValue)) is not None
    }


# the ordinary reader defaults to its first physical lane and honors explicit keyword names
def SelectLaneId(
    ConfigValues: Sequence[NativeConfig],
    Lanes: Mapping[int, str],
    Requested: str | None,
) -> int | None:
    if Requested is None:
        return 0 if 0 in Lanes else min(Lanes, default=None)
    return next(
        (Value.configuration_id for Value in ConfigValues if Value.name == Requested),
        None,
    )


# a legacy resolved carrier retains its priority over the native lane
def ResolvedStream(Streams: Mapping[str, bytes], LaneValue: str) -> str:
    return KitResolvedStream if KitResolvedStream in Streams else LaneValue
