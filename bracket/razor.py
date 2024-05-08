import build123d as bd
from bracket.socket import Socket, HoleProfile
from dataclasses import dataclass


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
    ) -> None:
        socket_size, socket_depth = Socket.calc_dimensions(hole_profile, wall_thickness)
        RazorBracket.validate_arguments(
            hole_profile,
            socket_size,
            socket_depth,
            slot_size,
            slot_offset,
            chamfers,
        )

        part = Socket(
            hole_profile=hole_profile,
            wall_thickness=wall_thickness,
            chamfers=slot_size if chamfers.sides else 0,
        ) - bd.extrude(
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

        def y_edges():
            nonlocal part
            return part.edges().group_by(bd.Axis.Y)

        if chamfers.slot:
            es = y_edges()
            part = bd.chamfer(
                [es[2].sort_by(bd.Axis.Z)[2:], es[4].sort_by(bd.Axis.Z)[2:]],
                chamfers.slot,
            )
        if chamfers.front:
            part = bd.chamfer(y_edges()[0] | bd.GeomType.LINE, chamfers.front)
        if chamfers.front_hole:
            part = bd.chamfer(y_edges()[0] | bd.GeomType.CIRCLE, chamfers.front_hole)
        if chamfers.back:
            part = bd.chamfer(y_edges()[-1] | bd.GeomType.LINE, chamfers.back)
        if chamfers.back_hole:
            part = bd.chamfer(y_edges()[-1] | bd.GeomType.CIRCLE, chamfers.back_hole)

        part.label = "Razor Bracket"
        super().__init__(part, rotation, align, mode)

    @staticmethod
    def validate_arguments(
        hole_profile: HoleProfile,
        socket_size: float,
        socket_depth: float,
        slot_size: float,
        slot_offset: float,
        chamfers: RazorBracketChamfers,
    ) -> None:
        if chamfers.front + chamfers.back >= socket_depth:
            raise ValueError(f"{(chamfers.front + chamfers.back)=} >= {socket_depth=}")
        if (
            chamfers.front_hole
            >= socket_size / 2 - hole_profile.first_section.radius - chamfers.front
        ):
            raise ValueError(
                f"{chamfers.front_hole=} >= "
                f"{(socket_size/2 - hole_profile.first_section.radius - chamfers.front)=}"
            )
        if chamfers.front_hole >= hole_profile.first_section.depth:
            raise ValueError(
                f"{chamfers.front_hole=} >= {hole_profile.first_section.depth=}"
            )
        if (
            chamfers.back_hole
            >= socket_size / 2 - hole_profile.last_section.radius - chamfers.back
        ):
            raise ValueError(
                f"{(chamfers.back_hole)=} >= "
                f"{(socket_size/2 - hole_profile.last_section.radius - chamfers.back)=}"
            )
        if chamfers.back_hole >= hole_profile.last_section.depth:
            raise ValueError(
                f"{chamfers.back_hole=} >= {hole_profile.last_section.depth=}"
            )
        if chamfers.slot + chamfers.front >= slot_offset:
            raise ValueError(f"{(chamfers.slot + chamfers.front)=} >= {slot_offset=}")
        if chamfers.slot >= slot_size:
            raise ValueError(f"{chamfers.slot=} >= {slot_size=}")
