from build123d import *
from bracket.socket import *


@dataclass
class RazorBracketChamfers:
    sides: bool = False
    front: float = 0
    front_hole: float = 0
    back: float = 0
    back_hole: float = 0
    slot: float = 0


class RazorBracket(BasePartObject):
    def __init__(
        self,
        hole_profile: HoleProfile,
        wall_thickness: float,
        slot_size: float,
        slot_offset: float = 0,
        chamfers: RazorBracketChamfers = RazorBracketChamfers(),
        rotation: RotationLike = (0, 0, 0),
        align: Align | tuple[Align, Align, Align] = Align.CENTER,
        mode: Mode = Mode.ADD,
    ):
        with BuildPart() as part_b:
            socket = Socket(
                hole_profile=hole_profile,
                wall_thickness=wall_thickness,
                sides_chamfer=slot_size if chamfers.sides else 0,
            )

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

            if chamfers.slot:
                x_edges = (
                    part_b.edges().filter_by(Axis.X).group_by(Axis.Z, reverse=True)
                )
                chamfer((x_edges[0] > Axis.Y)[1:3], chamfers.slot)
                chamfer((x_edges[1] > Axis.Y)[0:2], chamfers.slot)

            xz_faces = part_b.faces() | Plane.XZ > Axis.Y
            if chamfers.front:
                chamfer(xz_faces[0].edges() | GeomType.LINE, chamfers.front)
            if chamfers.front_hole:
                chamfer(xz_faces[0].edges() | GeomType.CIRCLE, chamfers.front_hole)
            if chamfers.back:
                chamfer(xz_faces[-1].edges() | GeomType.LINE, chamfers.back)
            if chamfers.back_hole:
                chamfer(xz_faces[-1].edges() | GeomType.CIRCLE, chamfers.back_hole)

        part_b.part.label = "Razor Bracket"
        super().__init__(part_b.part, rotation, align, mode)
