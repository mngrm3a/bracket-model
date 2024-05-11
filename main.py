import build123d as bd
import ocp_vscode as viewer
import os
import sys
from part import socket, slotted_socket, brush_bracket


HOLE_PROFILE = socket.HoleProfile(
    [
        (7, 4),  # nut top
        (4.5, 3),  # nut bottom
        (2, 2),  # screw / thread
        (8.5, 1.5),  # cup
    ]
)

assemblies = {
    "razor": slotted_socket.make_part(
        slotted_socket.Config(
            hole_profile=HOLE_PROFILE,
            wall_thickness=2,
            chamfers=slotted_socket.Chamfers(1, 1, 1, 1, 1, 0.5, 0),
            slot_size=1.5,
            slot_offset=2,
        ).validated()
    ),
    "brush": brush_bracket.make_part(
        brush_bracket.Config(
            hole_profile=HOLE_PROFILE,
            wall_thickness=2,
            chamfers=brush_bracket.Chamfers(1, 1),
            bracket_radius=15,
            bracket_offset=5,
            bracket_thickness=4,
            bracket_opening=120,
        ).validated()
    ),
}

if len(sys.argv) == 2:
    bd.export_step(slotted_socket, os.path.abspath(sys.argv[1]))
else:
    viewer.show(
        bd.pack(assemblies.values(), 2),
        measure_tools=False,
        render_joints=True,
        reset_camera=viewer.Camera.KEEP,
    )
