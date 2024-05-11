import build123d as bd
from part import socket, brush_bracket


def make_part(config: brush_bracket.Config) -> bd.Compound:
    config.chamfers.front = config.chamfers.front_hole = 0
    socket_part = socket.make_part(config)
    bracket_part = brush_bracket.make_part(config)

    socket_part.joints["center"].connect_to(bracket_part.joints["center"])
    return bd.Compound(label="Brush Holder", children=[socket_part, bracket_part])
