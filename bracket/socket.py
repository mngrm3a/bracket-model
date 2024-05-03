from build123d import *
from dataclasses import dataclass
import functools


@dataclass
class HoleSection:
    radius: float
    depth: float


HoleProfile = list[HoleSection]


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
        max_inner_radius, self.socket_depth = functools.reduce(
            lambda a, x: (max(a[0], x.radius), a[1] + x.depth),
            hole_profile,
            (0, 0),
        )
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
