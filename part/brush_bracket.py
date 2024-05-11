from dataclasses import dataclass
import itertools
import math
import build123d as bd
from part import socket
from typing_extensions import Self


@dataclass
class Config(socket.Config):
    bracket_radius: float
    bracket_offset: float
    bracket_thickness: float
    bracket_opening: float

    @property
    def bracket_height(self) -> float:
        return self.socket_size

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
        return self.socket_depth * 0.99

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
    part = bd.extrude(make_base_sketch(config), config.bracket_height) & bd.extrude(
        bd.Plane.YZ * make_profile_sketch(config),
        config.bracket_radius + config.bracket_thickness,
    )

    # def z_edges():
    #     nonlocal part
    #     return part.edges().filter_by(bd.Axis.Z, reverse=True).group_by(bd.Axis.Z)

    # if config.chamfers.bottom:
    #     part = bd.chamfer(
    #         (
    #             bd.ShapeList(itertools.chain(*z_edges()[:-1]))
    #             .sort_by(bd.Axis.X)[1 if config.bracket_opening else 2 :]
    #             .sort_by(bd.Axis.Y)[:-1]
    #         ),
    #         config.chamfers.bottom,
    #     )

    # if config.chamfers.top:
    #     part = bd.chamfer(
    #         z_edges()[-1]
    #         .sort_by(bd.Axis.X)[1 if config.bracket_opening else 2 :]
    #         .sort_by(bd.Axis.Y)[:-1],
    #         config.chamfers.top,
    #     )

    part -= (
        bd.Plane.XZ
        * bd.Pos(0, config.bracket_height - config.socket_size / 2)
        * bd.Hole(
            config.hole_profile.first_section.radius,
            config.bracket_radius + config.bracket_offset,
        )
    )

    # if config.chamfers.bottom:
    #     part = bd.chamfer(
    #         (
    #             part.edges()
    #             .filter_by(bd.GeomType.BSPLINE)
    #             .sort_by_distance(
    #                 (
    #                     0,
    #                     config.bracket_radius,
    #                     config.bracket_height - config.socket_size / 2,
    #                 ),
    #             )[0:3]
    #         ),
    #         config.chamfers.bottom,
    #     )

    # ! BUG: mirror fails when the top is chamfered but the left most edge above
    # ! the hole is not included.
    # * WORKAROUND: Add a small tolerance by offsetting the plane.
    # * SEE: https://discord.com/channels/964330484911972403/1074840524181217452/1237136617643442256
    part += bd.mirror(part, bd.Plane.YZ.offset(0.0001 if config.chamfers.top else 0))

    for j in [
        (
            "top",
            (0, config.bracket_radius + config.bracket_offset, config.bracket_height),
        ),
        (
            "center",
            (
                0,
                config.bracket_radius + config.bracket_offset,
                config.bracket_height - config.socket_size / 2,
            ),
        ),
    ]:
        bd.RigidJoint(
            j[0],
            part,
            bd.Location(j[1], bd.Plane.XZ.location.orientation),
        )
    part.label = "Brush Bracket"
    return part


def make_base_sketch(config: Config) -> bd.Sketch:
    socket_line = bd.Polyline(
        (0, config.bracket_radius),
        (0, config.bracket_radius + config.bracket_offset),
        (config.socket_size / 2, config.bracket_radius + config.bracket_offset),
        (
            config.socket_size / 2,
            config.bracket_radius
            + config.bracket_offset
            + config.socket_transition_depth,
        ),
    )
    outer_arc = bd.CenterArc(
        (0, 0),
        config.bracket_radius + config.bracket_thickness,
        config.socket_transition_angle,
        -(config.socket_transition_angle + config.tip_angle),
    )
    transition_line = bd.Spline(
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

    return bd.make_face([socket_line, transition_line, outer_arc, tip_line, inner_arc])


def make_profile_sketch(config: Config) -> bd.Sketch:
    tip_x = (
        -bd.polar(
            config.bracket_radius + config.bracket_thickness,
            90 - config.tip_angle,
        )[0]
        # NOTE avoid creating a separate face for the tip
        - config.tip_sagitta
        if config.bracket_opening
        else 0
    )

    profile0 = bd.Polyline(
        (
            config.bracket_radius
            + config.bracket_offset
            + config.socket_transition_depth,
            config.bracket_height,
        ),
        (config.bracket_radius + config.bracket_offset + config.socket_depth, 0),
        (config.bracket_radius + config.bracket_offset, 0),
    )
    profile1 = bd.Spline(
        profile0 @ 1,
        (tip_x, config.bracket_height - config.bracket_thickness),
        tangents=[(-0, 1), (-1, 0)],
    )
    profile2 = bd.Polyline(
        profile1 @ 1,
        (
            -(config.bracket_radius + config.bracket_thickness),
            config.bracket_height - config.bracket_thickness,
        ),
        (-(config.bracket_radius + config.bracket_thickness), config.bracket_height),
        profile0 @ 0,
    )

    return bd.make_face([profile0, profile1, profile2])
