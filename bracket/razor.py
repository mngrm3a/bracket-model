from typing import Iterable
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
        part = Socket(
            hole_profile=hole_profile,
            wall_thickness=wall_thickness,
            chamfers=slot_size if chamfers.sides else 0,
        )
        socket_size = part.socket_size
        socket_depth = part.socket_depth

        part -= bd.extrude(
            (
                bd.Plane.YZ
                * bd.Pos(
                    (-socket_depth + slot_size) / 2 + slot_offset,
                    (socket_size - slot_size) / 2,
                )
                * bd.Rectangle(slot_size, slot_size)
            ),
            socket_size / 2,
            both=True,
        )

        def chamfer_part(edges: Iterable[bd.Edge], length: float) -> None:
            nonlocal part
            part = part.chamfer(length=length, length2=None, edge_list=edges)

        if chamfers.slot:
            x_edges = (
                part.edges().filter_by(bd.Axis.X).group_by(bd.Axis.Z, reverse=True)
            )
            chamfer_part((x_edges[0] > bd.Axis.Y)[1:3], chamfers.slot)
            chamfer_part((x_edges[1] > bd.Axis.Y)[0:2], chamfers.slot)

        xz_edges = [f.edges() for f in part.faces() | bd.Plane.XZ > bd.Axis.Y]
        if chamfers.front:
            chamfer_part(xz_edges[0] | bd.GeomType.LINE, chamfers.front)
        if chamfers.front_hole:
            chamfer_part(xz_edges[0] | bd.GeomType.CIRCLE, chamfers.front_hole)
        if chamfers.back:
            chamfer_part(xz_edges[-1] | bd.GeomType.LINE, chamfers.back)
        if chamfers.back_hole:
            chamfer_part(xz_edges[-1] | bd.GeomType.CIRCLE, chamfers.back_hole)

        part.label = "Razor Bracket"
        super().__init__(part, rotation, align, mode)
