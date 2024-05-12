import argparse
import build123d as bd
import ocp_vscode as viewer
import pathlib
import tempfile
from part import socket, razor_bracket, brush_bracket

HOLE_PROFILE = socket.HoleProfile(
    [
        (7, 4),  # nut top
        (4.5, 3),  # nut bottom
        (2, 2),  # screw / thread
        (8.5, 1.5),  # cup
    ]
)


def assemblies() -> dict[str, bd.Part]:
    return {
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


def logged_io(path, io):
    try:
        print(f"Writing '{path}': ", end="")
        io(path)
        print("Ok")
    except Exception as e:
        print(f"Failed ({type(e).__name__})")


parser = argparse.ArgumentParser(description="Generate the bracket model.")
parser.add_argument(
    "action",
    choices=["export", "screenshot", "view"],
    default="view",
    help="action to perform",
)
parser.add_argument(
    "--dest",
    dest="destination",
    default=tempfile.gettempdir(),
    help="destination directory",
)
args = parser.parse_args()

match args.action:
    case "export":
        for path, assembly in [
            (
                str(pathlib.Path(args.destination).resolve().joinpath(f"{key}.step")),
                value,
            )
            for key, value in assemblies().items()
        ]:
            logged_io(path, lambda p: bd.export_step(assembly, p))
    case "screenshot":
        part = bd.Compound(children=bd.pack(assemblies().values(), 2))
        part_bbox = part.bounding_box()
        visible_edges, hidden_edges = part.project_to_viewport(
            part_bbox.center()
            + bd.polar(part_bbox.size.Y / 2, -145)
            + (0, 0, part_bbox.size.Z / 2)
        )
        max_dimension = max(
            *bd.Compound(children=visible_edges + hidden_edges).bounding_box().size
        )
        exporter = bd.ExportSVG(scale=2.5 * 100 / max_dimension)
        exporter.add_layer("Visible")
        exporter.add_layer(
            "Hidden", line_color=(99, 99, 99), line_type=bd.LineType.ISO_DOT
        )
        exporter.add_shape(visible_edges, layer="Visible")
        exporter.add_shape(hidden_edges, layer="Hidden")
        logged_io(
            pathlib.Path(args.destination).resolve().joinpath("screenshot.svg"),
            exporter.write,
        )
    case "view":
        viewer.show_object(
            bd.pack(assemblies().values(), 2),
            measure_tools=True,
            reset_camera=viewer.Camera.KEEP,
        )
