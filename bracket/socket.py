import collections.abc
import functools
from dataclasses import dataclass
import build123d as bd


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
        sides_chamfer: float = 0,
        rotation: bd.RotationLike = (0, 0, 0),
        align: bd.Align | tuple[bd.Align, bd.Align, bd.Align] = bd.Align.CENTER,
        mode: bd.Mode = bd.Mode.ADD,
    ):
        self.hole_profile = hole_profile
        max_inner_radius, self.socket_depth = hole_profile.outer_profile()
        self.socket_size = 2 * (max_inner_radius + wall_thickness)

        with bd.BuildPart() as part_b:
            with bd.BuildSketch(bd.Plane.XZ):
                r = bd.Rectangle(self.socket_size, self.socket_size)
                if sides_chamfer:
                    bd.chamfer(r.vertices(), sides_chamfer)
            bd.extrude(amount=self.socket_depth)

            for s in hole_profile:
                with bd.BuildSketch((part_b.faces() | bd.Plane.XZ > bd.Axis.Y)[-2:][0]):
                    bd.Circle(s.radius)
                bd.extrude(amount=-s.depth, mode=bd.Mode.SUBTRACT)

        bd.RigidJoint(
            "socket_joint",
            part_b.part,
            bd.Plane((part_b.faces() < bd.Axis.Y).last).location,
        )
        part_b.part.label = "Socket"
        super().__init__(part_b.part, rotation, align, mode)
