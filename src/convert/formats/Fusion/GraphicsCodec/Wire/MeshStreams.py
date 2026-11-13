from convert.formats.Fusion.GraphicsCodec.Model.State.GraphicsStream import (
    GraphicsStream,
)
from convert.formats.Fusion.GraphicsCodec.Wire.TransferSpanMut import TransferSpanMut
from convert.formats.Fusion.GraphicsCodec.Wire.FinishStreams import FinishStreams


class MeshStreams:
    def __init__(
        self,
        Streams: tuple[GraphicsStream, ...],
        IsReading: bool,
        Slack: tuple[GraphicsStream, ...] = (),
    ) -> None:
        super().__init__()
        self.IsReading = IsReading
        self.Inputs = {Entry.StreamIndex: Entry.Payload for Entry in Streams}
        self.Ranges: dict[int, dict[tuple[int, int], bytes]] = {}
        self.Tails = {Entry.StreamIndex: Entry.Payload for Entry in Slack}
        if (
            len(self.Inputs) != len(Streams)
            or len(self.Tails) != len(Slack)
            or any(
                type(Entry.StreamIndex) is not int
                or not 0 <= Entry.StreamIndex < 1000
                or type(Entry.Payload) is not bytes
                for Entry in Streams + Slack
            )
            or any(not Entry.Payload for Entry in Slack)
        ):
            raise ValueError("Invalid graphics mesh streams")

    def Transfer(
        self, Stream: int, Offset: int, Length: int, Payload: bytes | None
    ) -> bytes:
        return TransferSpanMut(self, Stream, Offset, Length, Payload)

    def Finalize(self) -> tuple[GraphicsStream, ...]:
        Streams, self.Tails = FinishStreams(self)
        return Streams

    def SlackValues(self) -> tuple[GraphicsStream, ...]:
        return tuple(
            GraphicsStream(Stream, Payload)
            for Stream, Payload in sorted(self.Tails.items())
        )
