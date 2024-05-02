from dataclasses import dataclass
import os
import sys
from build123d import *
from ocp_vscode import *
from bracket.razor import *


SOCKET_HOLE_SECTIONS = [
    HoleSection(7, 4),  # nut top
    HoleSection(4.5, 3),  # nut bottom
    HoleSection(2, 2),  # screw / thread
    HoleSection(8.5, 1.5),  # cup
]

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
        reset_camera=Camera.KEEP,
    )
