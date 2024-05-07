import collections.abc
import functools
from dataclasses import dataclass
from build123d import *


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


class Socket(BasePartObject):
    def __init__(
        self,
        hole_profile: HoleProfile,
        wall_thickness: float,
        sides_chamfer: float = 0,
        rotation: RotationLike = (0, 0, 0),
        align: Align | tuple[Align, Align, Align] = Align.CENTER,
        mode: Mode = Mode.ADD,
    ):
        max_inner_radius, self.socket_depth = hole_profile.outer_profile()
        self.socket_size = 2 * (max_inner_radius + wall_thickness)

        with BuildPart() as part_b:
            with BuildSketch(Plane.XZ):
                r = Rectangle(self.socket_size, self.socket_size)
                if sides_chamfer:
                    chamfer(r.vertices(), sides_chamfer)
            extrude(amount=self.socket_depth)

            for s in hole_profile:
                with BuildSketch((part_b.faces() | Plane.XZ > Axis.Y)[-2:][0]):
                    Circle(s.radius)
                extrude(amount=-s.depth, mode=Mode.SUBTRACT)

        RigidJoint(
            "socket_joint",
            part_b.part,
            Plane((part_b.faces() < Axis.Y).last).location,
        )
        part_b.part.label = "Socket"
        super().__init__(part_b.part, rotation, align, mode)
