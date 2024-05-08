from dataclasses import dataclass
import build123d as bd
from collections.abc import Iterable, Iterator


@dataclass
class HoleSection:
    radius: float = (0,)
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


class Socket(bd.BasePartObject):
    def __init__(
        self,
        hole_profile: HoleProfile,
        wall_thickness: float,
        chamfers: float = 0,
        rotation: bd.RotationLike = (0, 0, 0),
        align: bd.Align | tuple[bd.Align, bd.Align, bd.Align] = bd.Align.CENTER,
        mode: bd.Mode = bd.Mode.ADD,
    ):
        socket_size, socket_depth = Socket.calc_dimensions(hole_profile, wall_thickness)
        Socket.validate_arguments(wall_thickness, chamfers, socket_size)

        part = bd.Plane.ZX * bd.Rectangle(socket_size, socket_size)
        if chamfers:
            part = bd.chamfer(part.vertices(), chamfers)
        part = bd.extrude(part, socket_depth)

        for section in hole_profile:
            part -= bd.extrude(
                bd.Plane((part.faces() | bd.Plane.XZ > bd.Axis.Y)[-2:][0])
                * bd.Circle(section.radius),
                amount=-section.depth,
            )

        for j in [("top", (0, 0, socket_size / 2)), ("center", (0, 0, 0))]:
            bd.RigidJoint(
                j[0],
                part,
                bd.Location(j[1], bd.Plane.XZ.location.orientation),
            )
        part.label = "Socket"
        super().__init__(part, rotation, align, mode)

    @staticmethod
    def calc_dimensions(
        hole_profile: HoleProfile,
        wall_thickness: float,
    ) -> tuple[float, float]:
        return 2 * (hole_profile.max_radius + wall_thickness), hole_profile.depth

    @staticmethod
    def validate_arguments(
        wall_thickness: float,
        chamfers: float,
        socket_size: float,
    ) -> None:
        if wall_thickness < 0:
            raise ValueError(f"{wall_thickness=} < 0")
        if 2 * chamfers >= socket_size:
            raise ValueError(f"{(2 * chamfers)=} >= {socket_size}")
