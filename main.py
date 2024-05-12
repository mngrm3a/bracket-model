import build123d as bd
import ocp_vscode as viewer
import os
import sys
import pathlib
from part import socket, razor_bracket, brush_bracket


HOLE_PROFILE = socket.HoleProfile(
    [
        (7, 4),  # nut top
        (4.5, 3),  # nut bottom
        (2, 2),  # screw / thread
        (8.5, 1.5),  # cup
    ]
)

assemblies = {
    "razor": razor_bracket.make_part(
        razor_bracket.Config(
            hole_profile=HOLE_PROFILE,
            wall_thickness=2,
            slot_size=1.5,
            slot_offset=2,
            chamfers=razor_bracket.Chamfers(
                top=1,
                bottom=1,
                front=1,
                back=1,
                front_hole=1,
                back_hole=0.5,
                slot=0.5,
            ),
        ).validated()
    ),
    "brush": brush_bracket.make_part(
        brush_bracket.Config(
            hole_profile=HOLE_PROFILE,
            wall_thickness=2,
            bracket_radius=15,
            bracket_offset=5,
            bracket_thickness=4.5,
            bracket_opening=150,
            chamfers=brush_bracket.Chamfers(
                top=1,
                bottom=1,
                front=1,
                back=1,
                front_hole=1,
                back_hole=0.5,
            ),
        ).validated()
    ),
}


if len(sys.argv) == 2:
    output_dir = pathlib.Path(sys.argv[1]).resolve()
    if output_dir.is_dir() and os.access(output_dir, os.W_OK):
        for name, assembly in assemblies.items():
            output_file = output_dir.joinpath(f"{name}.step")
            print(f"Writing {output_file}")
            bd.export_step(assembly, str(output_dir.joinpath(f"{name}.step")))
else:
    viewer.show_object(
        bd.pack(assemblies.values(), 2),
        measure_tools=True,
        reset_camera=viewer.Camera.KEEP,
    )
