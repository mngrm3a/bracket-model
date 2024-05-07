import build123d as bd
import collections.abc
import functools
from dataclasses import dataclass


@dataclass
class HoleSection:
    radius: float
    depth: float


class HoleProfile(collections.abc.Iterable[HoleSection]):
    def __init__(self, items: list[HoleSection]):
        self.items = items

    def __init__(self, items: list[tuple[float, float]]):
        self.items = [HoleSection(item[0], item[1]) for item in items]

    def __iter__(self):
        return iter(self.items)

    def outer_profile(self) -> tuple[float, float]:
        return functools.reduce(
            lambda a, x: (max(a[0], x.radius), a[1] + x.depth),
            self,
            (0, 0),
        )


class Socket(bd.BasePartObject):
    def __init__(
        self,
        hole_profile: HoleProfile,
        wall_thickness: float,
        chamfers: float = 0,
        rotation: bd.RotationLike = (0, 0, 0),
        align: bd.Align | tuple[bd.Align, bd.Align, bd.Align] = bd.Align.CENTER,
        mode: bd.Mode = bd.Mode.ADD,
    ):
        self.hole_profile = hole_profile
        max_hole_radius, self.socket_depth = hole_profile.outer_profile()
        self.socket_size = 2 * (max_hole_radius + wall_thickness)

        part = bd.Plane.ZX * bd.Rectangle(self.socket_size, self.socket_size)
        if chamfers:
            part = bd.chamfer(part.vertices(), chamfers)
        part = bd.extrude(part, self.socket_depth)

        for section in self.hole_profile:
            part -= bd.extrude(
                bd.Plane((part.faces() | bd.Plane.XZ > bd.Axis.Y)[-2:][0])
                * bd.Circle(section.radius),
                amount=-section.depth,
            )

        for j in [("top", (0, 0, self.socket_size / 2)), ("center", (0, 0, 0))]:
            bd.RigidJoint(
                j[0],
                part,
                bd.Location(j[1], bd.Plane.XZ.location.orientation),
            )
        part.label = "Socket"
        super().__init__(part, rotation, align, mode)
