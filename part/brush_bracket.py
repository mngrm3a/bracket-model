import build123d as bd
import itertools
import math
from dataclasses import dataclass
from part import socket
from typing_extensions import Self


@dataclass
class Chamfers(socket.Chamfers):
    pass


@dataclass
class Config(socket.Config):
    bracket_radius: float
    bracket_offset: float
    bracket_thickness: float
    bracket_opening: float

    @property
    def bracket_height(self) -> float:
        return 0.75 * self.socket_size

    @property
    def socket_transition_angle(self) -> float:
        def chord(radius: float, sagitta: float) -> float:
            return math.sqrt(2 * radius * sagitta - sagitta**2)

        point = bd.Vector(
            chord(self.bracket_radius + self.bracket_thickness, self.bracket_thickness),
            self.bracket_radius,
            0,
        )

        return bd.Axis.X.direction.get_angle(point) / 2

    @property
    def socket_transition_depth(self) -> float:
        return self.socket_depth

    @property
    def tip_angle(self) -> float:
        return 90 - (self.bracket_opening / 2)

    @property
    def tip_sagitta(self) -> float:
        return self.bracket_thickness / 2

    def validated(self) -> Self:
        if not (
            self.bracket_opening >= 15
            and self.bracket_opening <= 180
            or self.bracket_opening == 0
        ):
            raise ValueError(
                f"Range({self.bracket_opening=}): 15 <= VALUE <= 180 || VALUE == 0"
            )
        if self.bracket_radius < self.socket_size / 2:
            raise ValueError(f"{self.bracket_radius=} < {(self.socket_size/2)=}")

        if self.chamfers.top >= self.bracket_offset:
            raise ValueError(f"{self.chamfers.top=} >= {self.bracket_offset=}")
        if 2 * self.chamfers.top >= self.bracket_thickness:
            raise ValueError(f"{(2 * self.chamfers.top)=} >= {self.bracket_thickness=}")

        if 2 * self.chamfers.bottom >= self.bracket_thickness:
            raise ValueError(
                f"{(2 * self.chamfers.bottom)=} >= {self.bracket_thickness=}"
            )

        # hole
        if self.chamfers.bottom > self.hole_profile.first_section.radius:
            raise ValueError(
                f"{self.chamfers.bottom=} > {self.hole_profile.first_section.radius=}"
            )
        if self.chamfers.bottom >= self.bracket_offset:
            raise ValueError(f"{self.chamfers.bottom=} >= {self.bracket_offset=}")
        if (
            self.chamfers.bottom + self.hole_profile.first_section.radius
            >= self.socket_size / 2
        ):
            raise ValueError(
                f"{(self.chamfers.bottom + self.hole_profile.first_section.radius)=} >= {(self.socket_size/2)=}"
            )

        return self


def make_part(config: Config) -> bd.Part:
    part = bd.extrude(make_base_sketch(config), config.socket_size) & bd.extrude(
        bd.Plane.YZ * make_profile_sketch(config),
        config.bracket_radius + config.bracket_thickness,
    )

    def z_edges():
        nonlocal part
        return part.edges().filter_by(bd.Axis.Z, reverse=True).group_by(bd.Axis.Z)

    if config.chamfers.bottom:
        part = bd.chamfer(
            (
                bd.ShapeList(itertools.chain(*z_edges()[:-1]))
                .sort_by(bd.Axis.Y)[:-1]
                .sort_by(bd.Axis.X)[3 if config.bracket_opening else 4 :]
            ),
            config.chamfers.bottom,
        )

    if config.chamfers.top:
        part = bd.chamfer(
            z_edges()[-1]
            .sort_by(bd.Axis.Y)[:-1]
            .sort_by(bd.Axis.X)[1 if config.bracket_opening else 2 :],
            config.chamfers.top,
        )

    if config.chamfers.front:
        part = bd.chamfer(
            z_edges()[0].sort_by(bd.Axis.Y)[0],
            config.chamfers.front,
        )

    if config.chamfers.back:
        part = bd.chamfer(
            part.edges().group_by(bd.Axis.Y)[-1].sort_by(bd.Axis.X)[1:],
            config.chamfers.back,
        )

    hole_y = (
        config.bracket_radius
        + config.bracket_offset
        + config.socket_depth
        - config.hole_profile.depth
    )
    for section in config.hole_profile:
        part -= bd.extrude(
            bd.Pos(0, hole_y, config.socket_size / 2)
            * bd.Rot(90)
            * bd.Circle(section.radius),
            amount=-section.depth,
        )
        hole_y += section.depth
    part -= (
        bd.Plane.XZ
        * bd.Pos(0, config.socket_size / 2)
        * bd.Hole(
            config.hole_profile.first_section.radius,
            config.bracket_radius + config.bracket_offset,
        )
    )

    if config.chamfers.front_hole:
        part = bd.chamfer(
            part.edges()
            .filter_by(
                lambda e: (
                    e.geom_type == bd.GeomType.BSPLINE
                    or e.geom_type == bd.GeomType.CIRCLE
                )
                and e.center().Y <= config.bracket_radius + config.bracket_offset
                and e.center().Y >= config.bracket_radius - 1
            )
            .sort_by_distance((0, config.bracket_radius, config.socket_size / 2))[
                0 : 4 if config.chamfers.bottom else 3
            ],
            config.chamfers.front_hole,
        )

    if config.chamfers.back_hole:
        part = bd.chamfer(
            part.edges().filter_by(bd.GeomType.CIRCLE).group_by(bd.Axis.Y)[-1],
            config.chamfers.back_hole,
        )

    part += bd.mirror(part, bd.Plane.YZ)

    part.label = "Brush Bracket"
    return part


def make_base_sketch(config: Config) -> bd.Sketch:
    socket_line = bd.Polyline(
        (0, config.bracket_radius),
        (0, config.bracket_radius + config.bracket_offset + config.socket_depth),
        (
            config.socket_size / 2,
            config.bracket_radius + config.bracket_offset + config.socket_depth,
        ),
    )
    outer_arc = bd.CenterArc(
        (0, 0),
        config.bracket_radius + config.bracket_thickness,
        config.socket_transition_angle,
        -(config.socket_transition_angle + config.tip_angle),
    )
    transition_spline = bd.Spline(
        socket_line @ 1,
        outer_arc @ 0,
        tangents=[(0, -1), outer_arc.tangent_at(outer_arc @ 0)],
        tangent_scalars=[1, 1],
    )
    inner_arc = bd.CenterArc(
        (0, 0),
        config.bracket_radius,
        -config.tip_angle,
        config.tip_angle + 90,
    )
    if config.bracket_opening:
        tip_line = bd.SagittaArc(
            outer_arc @ 1,
            inner_arc @ 0,
            config.tip_sagitta,
        )
    else:
        tip_line = bd.Line(outer_arc @ 1, inner_arc @ 0)

    return bd.make_face(
        [socket_line, transition_spline, outer_arc, tip_line, inner_arc]
    )


def make_profile_sketch(config: Config) -> bd.Sketch:
    tip_x = (
        -bd.polar(
            config.bracket_radius + config.bracket_thickness,
            90 - config.tip_angle,
        )[0]
        # NOTE: avoid creating a separate face for the tip
        - config.tip_sagitta
        if config.bracket_opening
        else 0
    )
    profile0_points = [
        (
            config.bracket_radius + config.bracket_offset + config.socket_depth,
            config.socket_size,
        ),
        (config.bracket_radius + config.bracket_offset + config.socket_depth, 0),
        (config.bracket_radius + config.bracket_offset, 0),
    ]
    if config.socket_size > config.bracket_height:
        profile0_points.append(
            (
                config.bracket_radius + config.bracket_offset,
                config.socket_size - config.bracket_height,
            ),
        )

    profile0 = bd.Polyline(profile0_points)
    profile1 = bd.Spline(
        profile0 @ 1,
        (tip_x, config.socket_size - config.bracket_thickness),
        tangents=[(0, 1), (-1, 0)],
        tangent_scalars=[1, 1.5],
    )
    profile2 = bd.Polyline(
        profile1 @ 1,
        (
            -(config.bracket_radius + config.bracket_thickness),
            config.socket_size - config.bracket_thickness,
        ),
        (-(config.bracket_radius + config.bracket_thickness), config.socket_size),
        profile0 @ 0,
    )

    return bd.make_face([profile0, profile1, profile2])
