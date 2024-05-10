import build123d as bd
from dataclasses import dataclass
from holder.hole import HoleProfile
from holder.socket import Socket, SocketChamfers


@dataclass
class RazorHolderChamfers(SocketChamfers):
    slot: float = 0


class RazorHolder(bd.BasePartObject):
    def __init__(
        self,
        hole_profile: HoleProfile,
        wall_thickness: float,
        slot_size: float,
        slot_offset: float = 0,
        chamfers: RazorHolderChamfers = RazorHolderChamfers(),
        rotation: bd.RotationLike = (0, 0, 0),
        align: bd.Align | tuple[bd.Align, bd.Align, bd.Align] = bd.Align.CENTER,
        mode: bd.Mode = bd.Mode.ADD,
    ) -> None:
        self.__slot_size = slot_size
        self.__slot_offset = slot_offset
        self.__chamfers = chamfers
        self.__validate()

        part = Socket(
            hole_profile,
            wall_thickness,
            SocketChamfers(
                top=slot_size if self.chamfers.top else 0,
                bottom=slot_size if self.chamfers.bottom else 0,
                front=self.chamfers.front,
                back=self.chamfers.back,
                front_hole=self.chamfers.front_hole,
                back_hole=self.chamfers.back_hole,
            ),
        )

        part -= bd.extrude(
            (
                bd.Plane.YZ
                * bd.Pos(
                    (-part.socket_depth + self.slot_size) / 2 + self.slot_offset,
                    (part.socket_size - self.slot_size) / 2,
                )
                * bd.Rectangle(self.slot_size, self.slot_size)
            ),
            part.socket_size / 2,
            both=True,
        )

        if chamfers.slot:
            part = bd.chamfer(
                (
                    part.edges()
                    .filter_by(bd.Axis.X)
                    .group_by(bd.Axis.Z)[-1]
                    .sort_by(bd.Axis.Y)
                )[1:3],
                chamfers.slot,
            )

        part.label = "Razor Bracket"
        super().__init__(part, rotation, align, mode)

    @property
    def slot_size(self) -> float:
        return self.__slot_size

    @property
    def slot_offset(self) -> float:
        return self.__slot_offset

    @property
    def chamfers(self) -> RazorHolderChamfers:
        return self.__chamfers

    def __validate(self) -> None:
        if self.chamfers.slot + self.chamfers.front >= self.slot_offset:
            raise ValueError(
                f"{(self.chamfers.slot + self.chamfers.front)=} >= {self.slot_offset=}"
            )
        if self.chamfers.slot >= self.slot_size:
            raise ValueError(f"{self.chamfers.slot=} >= {self.slot_size=}")
