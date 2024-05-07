import build123d as bd
from dataclasses import dataclass
from bracket.socket import Socket, HoleProfile


@dataclass
class RazorBracketChamfers:
    sides: bool = False
    front: float = 0
    front_hole: float = 0
    back: float = 0
    back_hole: float = 0
    slot: float = 0


class RazorBracket(bd.BasePartObject):
    def __init__(
        self,
        hole_profile: HoleProfile,
        wall_thickness: float,
        slot_size: float,
        slot_offset: float = 0,
        chamfers: RazorBracketChamfers = RazorBracketChamfers(),
        rotation: bd.RotationLike = (0, 0, 0),
        align: bd.Align | tuple[bd.Align, bd.Align, bd.Align] = bd.Align.CENTER,
        mode: bd.Mode = bd.Mode.ADD,
    ):
        with bd.BuildPart() as part_b:
            socket = Socket(
                hole_profile=hole_profile,
                wall_thickness=wall_thickness,
                chamfers=slot_size if chamfers.sides else 0,
            )

            with bd.BuildSketch(bd.Plane.YZ):
                with bd.Locations(
                    (
                        (-socket.socket_depth + slot_size) / 2 + slot_offset,
                        (socket.socket_size - slot_size) / 2,
                        0,
                    )
                ):
                    bd.Rectangle(slot_size, slot_size)
            bd.extrude(until=bd.Until.LAST, both=True, mode=bd.Mode.SUBTRACT)

            if chamfers.slot:
                x_edges = (
                    part_b.edges()
                    .filter_by(bd.Axis.X)
                    .group_by(bd.Axis.Z, reverse=True)
                )
                bd.chamfer((x_edges[0] > bd.Axis.Y)[1:3], chamfers.slot)
                bd.chamfer((x_edges[1] > bd.Axis.Y)[0:2], chamfers.slot)

            xz_faces = part_b.faces() | bd.Plane.XZ > bd.Axis.Y
            if chamfers.front:
                bd.chamfer(xz_faces[0].edges() | bd.GeomType.LINE, chamfers.front)
            if chamfers.front_hole:
                bd.chamfer(
                    xz_faces[0].edges() | bd.GeomType.CIRCLE, chamfers.front_hole
                )
            if chamfers.back:
                bd.chamfer(xz_faces[-1].edges() | bd.GeomType.LINE, chamfers.back)
            if chamfers.back_hole:
                bd.chamfer(
                    xz_faces[-1].edges() | bd.GeomType.CIRCLE, chamfers.back_hole
                )

        part_b.part.label = "Razor Bracket"
        super().__init__(part_b.part, rotation, align, mode)
