from copy import copy
from dataclasses import dataclass
from typing_extensions import Self
import build123d as bd
from part import socket, brush_bracket
import ocp_vscode as viewer


class Config(brush_bracket.Config):
    def validated(self) -> Self:
        return self


def make_part(config: brush_bracket.Config) -> bd.Part:
    socket_config = copy(config)
    socket_config.chamfers = socket.Chamfers(
        0, 0, 0, 0, 0, socket_config.chamfers.back_hole
    )
    socket_part = socket.make_part(socket_config)
    bracket_part = brush_bracket.make_part(config)

    socket_part.joints["center"].connect_to(bracket_part.joints["center"])
    part = socket_part + bracket_part
    # part = bd.Compound(label="Brush Holder", children=[socket_part, bracket_part])

    def z_edges():
        nonlocal part
        return part.edges().filter_by(bd.Axis.Z, reverse=True).group_by(bd.Axis.Z)

    # if config.chamfers.top:
    #     es = z_edges()[-1].filter_by(bd.Axis.X, reverse=True)
    #     viewer.show_object(es)
    # part = bd.chamfer(
    #     z_edges()[-1].filter_by(bd.Axis.X, reverse=True),
    #     config.chamfers.top,
    # )
    # viewer.show_object(z_edges()[-1].filter_by(bd.Axis.X, reverse=True))

    return part
