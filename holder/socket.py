import build123d as bd
from dataclasses import dataclass
from holder.hole import HoleProfile
from typing_extensions import Self


@dataclass
class Chamfers:
    top: float = 0
    bottom: float = 0
    front: float = 0
    back: float = 0
    front_hole: float = 0
    back_hole: float = 0


@dataclass
class Config:
    hole_profile: HoleProfile
    wall_thickness: float
    chamfers: Chamfers

    @property
    def socket_size(self) -> float:
        return 2 * (self.hole_profile.max_radius + self.wall_thickness)

    @property
    def socket_depth(self) -> float:
        return self.hole_profile.depth

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

    for j in [("top", (0, 0, config.socket_size / 2)), ("center", (0, 0, 0))]:
        bd.RigidJoint(
            j[0],
            part,
            bd.Location(j[1], bd.Plane.XZ.location.orientation),
        )

    part.label = "Socket"
    return part
