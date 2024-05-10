import build123d as bd
import holder.socket
from dataclasses import dataclass
from typing_extensions import Self


@dataclass
class Chamfers(holder.socket.Chamfers):
    slot: float = 0


@dataclass
class Config(holder.socket.Config):
    chamfers: Chamfers
    slot_size: float
    slot_offset: float

    def validated(self) -> Self:
        if self.chamfers.slot + self.chamfers.front >= self.slot_offset:
            raise ValueError(
                f"{(self.chamfers.slot + self.chamfers.front)=} >= {self.slot_offset=}"
            )
        if self.chamfers.slot >= self.slot_size:
            raise ValueError(f"{self.chamfers.slot=} >= {self.slot_size=}")

        super().validated()
        return self


def make_part(config: Config) -> bd.Part:
    print(config.socket_depth)
    part = holder.socket.make_part(config) - bd.extrude(
        (
            bd.Plane.YZ
            * bd.Pos(
                config.slot_offset + config.slot_size / 2,
                (config.socket_size - config.slot_size) / 2,
            )
            * bd.Rectangle(config.slot_size, config.slot_size)
        ),
        config.socket_size / 2,
        both=True,
    )

    if config.chamfers.slot:
        part = bd.chamfer(
            (
                part.edges()
                .filter_by(bd.Axis.X)
                .group_by(bd.Axis.Z)[-1]
                .sort_by(bd.Axis.Y)
            )[1:3],
            config.chamfers.slot,
        )

    part.label = "Razor Bracket"
    return part
