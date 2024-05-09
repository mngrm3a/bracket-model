import build123d as bd
import ocp_vscode as viewer
import os
import sys
from holder.razor import RazorHolder, RazorHolderChamfers
from holder.socket import HoleProfile


SOCKET_HOLE_SECTIONS = HoleProfile(
    [
        (7, 4),  # nut top
        (4.5, 3),  # nut bottom
        (2, 2),  # screw / thread
        (8.5, 1.5),  # cup
    ]
)

result = RazorHolder(
    hole_profile=SOCKET_HOLE_SECTIONS,
    wall_thickness=2,
    slot_size=1.5,
    slot_offset=2,
    chamfers=RazorHolderChamfers(1, 1, 1, 1, 1, 0.5, 0.5),
)

if len(sys.argv) == 2:
    bd.export_step(result, os.path.abspath(sys.argv[1]))
else:
    viewer.show(
        result,
        measure_tools=True,
        render_joints=True,
        reset_camera=viewer.Camera.KEEP,
    )
