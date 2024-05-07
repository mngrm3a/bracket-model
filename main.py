import os
import sys
from ocp_vscode import show, Camera
from build123d import *
from bracket.socket import HoleProfile
from bracket.razor import RazorBracket, RazorBracketChamfers


SOCKET_HOLE_SECTIONS = HoleProfile(
    [
        (7, 4),  # nut top
        (4.5, 3),  # nut bottom
        (2, 2),  # screw / thread
        (8.5, 1.5),  # cup
    ]
)

result = RazorBracket(
    hole_profile=SOCKET_HOLE_SECTIONS,
    wall_thickness=2,
    slot_size=1.5,
    slot_offset=2,
    chamfers=RazorBracketChamfers(
        sides=True, front=1, front_hole=1, back=1, back_hole=0.5, slot=0
    ),
)
if len(sys.argv) == 2:
    export_step(result, os.path.abspath(sys.argv[1]))
else:
    show(
        result,
        measure_tools=True,
        render_joints=True,
        reset_camera=Camera.KEEP,
    )
