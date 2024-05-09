import build123d as bd
from collections.abc import Iterable, Iterator
from dataclasses import dataclass


@dataclass
class HoleSection:
    radius: float = 0
    depth: float = 0


class HoleProfile(Iterable[HoleSection]):
    def __init__(self, items: Iterable[tuple[float, float]]) -> None:
        if not len(items):
            raise ValueError(f"items must not be empty")
        self._max_radius: float = 0
        self._depth: float = 0
        for item in items:
            if item[0] <= 0 or item[1] <= 0:
                raise ValueError(f"radius or depth <= 0: ${item}")
            self._max_radius = max(self._max_radius, item[0])
            self._depth += item[1]
        self._items: list[HoleSection] = [HoleSection(i[0], i[1]) for i in items]

    def __iter__(self) -> Iterator[HoleSection]:
        return iter(self._items)

    @property
    def max_radius(self) -> float:
        return self._max_radius

    @property
    def depth(self) -> float:
        return self._depth

    @property
    def first_section(self) -> HoleSection:
        return self._items[0]

    @property
    def last_section(self) -> HoleSection:
        return self._items[-1]


@dataclass
class Chamfers:
    top: float = 0
    bottom: float = 0


@dataclass
class SocketChamfers(Chamfers):
    front: float = 0
    back: float = 0
    front_hole: float = 0
    back_hole: float = 0


class Socket(bd.BasePartObject):
    def __init__(
        self,
        hole_profile: HoleProfile,
        wall_thickness: float,
        chamfers: SocketChamfers = SocketChamfers(),
        rotation: bd.RotationLike = (0, 0, 0),
        align: bd.Align | tuple[bd.Align, bd.Align, bd.Align] = bd.Align.CENTER,
        mode: bd.Mode = bd.Mode.ADD,
    ):
        self.__hole_profile = hole_profile
        self.__wall_thickness = wall_thickness
        self.__chamfers = chamfers
        self.__validate()

        part = bd.Plane.ZX * bd.Rectangle(self.socket_size, self.socket_size)
        if chamfers.top:
            part = bd.chamfer(part.vertices() >> bd.Axis.Z, chamfers.top)
        if chamfers.bottom:
            part = bd.chamfer(part.vertices() << bd.Axis.Z, chamfers.bottom)
        part = bd.extrude(part, self.socket_depth)

        for section in hole_profile:
            part -= bd.extrude(
                bd.Plane((part.faces() | bd.Plane.XZ > bd.Axis.Y)[-2:][0])
                * bd.Circle(section.radius),
                amount=-section.depth,
            )

        def y_edges():
            nonlocal part
            return part.edges().group_by(bd.Axis.Y)

        if chamfers.front:
            part = bd.chamfer(y_edges()[0] | bd.GeomType.LINE, chamfers.front)
        if chamfers.front_hole:
            part = bd.chamfer(y_edges()[0] | bd.GeomType.CIRCLE, chamfers.front_hole)
        if chamfers.back:
            part = bd.chamfer(y_edges()[-1] | bd.GeomType.LINE, chamfers.back)
        if chamfers.back_hole:
            part = bd.chamfer(y_edges()[-1] | bd.GeomType.CIRCLE, chamfers.back_hole)

        for j in [("top", (0, 0, self.socket_size / 2)), ("center", (0, 0, 0))]:
            bd.RigidJoint(
                j[0],
                part,
                bd.Location(j[1], bd.Plane.XZ.location.orientation),
            )
        part.label = "Socket"
        super().__init__(part, rotation, align, mode)

    @property
    def hole_profile(self) -> HoleProfile:
        return self.__hole_profile

    @property
    def wall_thickness(self) -> float:
        return self.__wall_thickness

    @property
    def chamfers(self) -> SocketChamfers:
        return self.__chamfers

    @property
    def socket_size(self) -> float:
        return 2 * (self.hole_profile.max_radius + self.wall_thickness)

    @property
    def socket_depth(self) -> float:
        return self.hole_profile.depth

    def __validate(self) -> None:
        if self.wall_thickness < 0:
            raise ValueError(f"{self.wall_thickness=} < 0")

        if self.chamfers.top + self.chamfers.bottom >= self.socket_size:
            raise ValueError(
                f"{(self.chamfers.top + self.chamfers.bottom)=} >= {self.socket_size=}"
            )

        if self.chamfers.front + self.chamfers.back >= self.socket_depth:
            raise ValueError(
                f"{(self.chamfers.front + self.chamfers.back)=} >= {self.socket_depth=}"
            )

        if (
            self.chamfers.front_hole
            >= self.socket_size / 2
            - self.hole_profile.first_section.radius
            - self.chamfers.front
        ):
            raise ValueError(
                f"{self.chamfers.front_hole=} >= "
                f"{(self.socket_size/2 - self.hole_profile.first_section.radius - self.chamfers.front)=}"
            )
        if self.chamfers.front_hole >= self.hole_profile.first_section.depth:
            raise ValueError(
                f"{self.chamfers.front_hole=} >= {self.hole_profile.first_section.depth=}"
            )

        if (
            self.chamfers.back_hole
            >= self.socket_size / 2
            - self.hole_profile.last_section.radius
            - self.chamfers.back
        ):
            raise ValueError(
                f"{(self.chamfers.back_hole)=} >= "
                f"{(self.socket_size/2 - self.hole_profile.last_section.radius - self.chamfers.back)=}"
            )
        if self.chamfers.back_hole >= self.hole_profile.last_section.depth:
            raise ValueError(
                f"{self.chamfers.back_hole=} >= {self.hole_profile.last_section.depth=}"
            )
