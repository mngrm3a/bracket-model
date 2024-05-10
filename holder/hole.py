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
