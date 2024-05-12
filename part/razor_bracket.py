import build123d as bd
from dataclasses import dataclass
from part import socket
from typing_extensions import Self


@dataclass
class Chamfers(socket.Chamfers):
    slot: float = 0


@dataclass
class Config(socket.Config):
    slot_size: float
    slot_offset: float
    chamfers: Chamfers

    def validated(self) -> Self:
        if self.wall_thickness < 0:
            raise ValueError(f"{self.wall_thickness=} < 0")

        if self.chamfers.top + self.chamfers.bottom >= self.socket_size:
            raise ValueError(
                f"{(self.chamfers.top + self.chamfers.bottom)=} >= {self.socket_size=}"
            )

        if self.chamfers.front + self.chamfers.back >= self.socket_depth:
            raise ValueError(
                f"{(self.chamfers.front + self.chamfers.back)=} >= {self.socket_depth=}"
            )

        if (
            self.chamfers.front_hole
            >= self.socket_size / 2
            - self.hole_profile.first_section.radius
            - self.chamfers.front
        ):
            raise ValueError(
                f"{self.chamfers.front_hole=} >= "
                f"{(self.socket_size/2 - self.hole_profile.first_section.radius - self.chamfers.front)=}"
            )
        if self.chamfers.front_hole >= self.hole_profile.first_section.depth:
            raise ValueError(
                f"{self.chamfers.front_hole=} >= {self.hole_profile.first_section.depth=}"
            )

        if (
            self.chamfers.back_hole
            >= self.socket_size / 2
            - self.hole_profile.last_section.radius
            - self.chamfers.back
        ):
            raise ValueError(
                f"{(self.chamfers.back_hole)=} >= "
                f"{(self.socket_size/2 - self.hole_profile.last_section.radius - self.chamfers.back)=}"
            )
        if self.chamfers.back_hole >= self.hole_profile.last_section.depth:
            raise ValueError(
                f"{self.chamfers.back_hole=} >= {self.hole_profile.last_section.depth=}"
            )

        if self.chamfers.slot + self.chamfers.front >= self.slot_offset:
            raise ValueError(
                f"{(self.chamfers.slot + self.chamfers.front)=} >= {self.slot_offset=}"
            )
        if self.chamfers.slot >= self.slot_size:
            raise ValueError(f"{self.chamfers.slot=} >= {self.slot_size=}")

        return self


def make_part(config: Config) -> bd.Part:
    part = bd.Plane.ZX * bd.Rectangle(config.socket_size, config.socket_size)
    if config.chamfers.top:
        part = bd.chamfer(part.vertices() >> bd.Axis.Z, config.chamfers.top)
    if config.chamfers.bottom:
        part = bd.chamfer(part.vertices() << bd.Axis.Z, config.chamfers.bottom)
    part = bd.extrude(part, config.socket_depth)

    for section in config.hole_profile:
        part -= bd.extrude(
            bd.Plane((part.faces() | bd.Plane.XZ > bd.Axis.Y)[-2:][0])
            * bd.Circle(section.radius),
            amount=-section.depth,
        )

    def y_edges():
        nonlocal part
        return part.edges().group_by(bd.Axis.Y)

    if config.chamfers.front:
        part = bd.chamfer(y_edges()[0] | bd.GeomType.LINE, config.chamfers.front)
    if config.chamfers.front_hole:
        part = bd.chamfer(y_edges()[0] | bd.GeomType.CIRCLE, config.chamfers.front_hole)
    if config.chamfers.back:
        part = bd.chamfer(y_edges()[-1] | bd.GeomType.LINE, config.chamfers.back)
    if config.chamfers.back_hole:
        part = bd.chamfer(y_edges()[-1] | bd.GeomType.CIRCLE, config.chamfers.back_hole)

    part -= bd.extrude(
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
