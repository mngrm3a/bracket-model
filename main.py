from dataclasses import dataclass
import functools
import os
import sys
from build123d import *
from ocp_vscode import *


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
        edge_chamfer: float = 0,
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
                if edge_chamfer > 0:
                    chamfer(r.vertices(), edge_chamfer)
            extrude(amount=self.socket_depth)

            for s in hole_profile:
                with BuildSketch((part_b.faces() | Plane.XZ > Axis.Y)[-2:][0]):
                    Circle(s.radius)
                extrude(amount=-s.depth, mode=Mode.SUBTRACT)

        part_b.part.label = "Socket"
        super().__init__(part_b.part, rotation, align, mode)


class RazorBracket(BasePartObject):
    def __init__(
        self,
        hole_profile: HoleProfile,
        wall_thickness: float,
        slot_size: float,
        slot_offset: float = 0,
        edge_chamfer: float = 0,
        rotation: RotationLike = (0, 0, 0),
        align: Align | tuple[Align, Align, Align] = Align.CENTER,
        mode: Mode = Mode.ADD,
    ):
        with BuildPart() as part_b:
            socket = Socket(hole_profile, wall_thickness, slot_size)

            with BuildSketch(Plane.YZ):
                with Locations(
                    (
                        (-socket.socket_depth + slot_size) / 2 + slot_offset,
                        (socket.socket_size - slot_size) / 2,
                        0,
                    )
                ):
                    Rectangle(slot_size, slot_size)
            extrude(until=Until.LAST, both=True, mode=Mode.SUBTRACT)

            if edge_chamfer > 0:
                # x_edges = (
                #     part_b.edges().filter_by(Axis.X).group_by(Axis.Z, reverse=True)
                # )
                # chamfer((x_edges[0] > Axis.Y)[1:3], edge_chamfer / 2)
                # chamfer((x_edges[1] > Axis.Y)[0:2], edge_chamfer / 2)

                xz_faces = part_b.faces() | Plane.XZ > Axis.Y
                chamfer(xz_faces[0].edges(), edge_chamfer)
                chamfer(xz_faces[-1].edges() | GeomType.LINE, edge_chamfer)
                chamfer(xz_faces[-1].edges() | GeomType.CIRCLE, edge_chamfer / 2)

        part_b.part.label = "Razor Bracket"
        super().__init__(part_b.part, rotation, align, mode)


SOCKET_HOLE_SECTIONS = [
    HoleSection(7, 4),  # nut top
    HoleSection(4.5, 3),  # nut bottom
    HoleSection(2, 2),  # screw / thread
    HoleSection(8.5, 1.5),  # cup
]

result = RazorBracket(
    hole_profile=SOCKET_HOLE_SECTIONS,
    wall_thickness=2,
    slot_size=1.5,
    slot_offset=2,
    edge_chamfer=1,
)
if len(sys.argv) == 2:
    export_step(result, os.path.abspath(sys.argv[1]))
else:
    show(
        result,
        measure_tools=True,
        reset_camera=Camera.KEEP,
    )
