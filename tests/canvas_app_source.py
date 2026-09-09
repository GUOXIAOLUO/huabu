"""Shared source view for the ordered R4 Canvas application modules."""

from pathlib import Path


CANVAS_APP_RELATIVE_PATHS = (
    "static/js/workbench/canvas/canvas-app-state.js",
    "static/js/workbench/canvas/canvas-app-records.js",
    "static/js/workbench/canvas/canvas-app-media-editor.js",
    "static/js/workbench/canvas/canvas-app-compat-host.js",
    "static/js/workbench/canvas/canvas-app-provider-ui.js",
    "static/js/workbench/canvas/canvas-app-execution.js",
    "static/js/workbench/canvas/canvas-app-output-ui.js",
    "static/js/workbench/canvas/canvas-app-interaction.js",
    "static/js/workbench/canvas/canvas-app-bootstrap.js",
)


def canvas_app_paths(root: Path) -> tuple[Path, ...]:
    return tuple(root / relative for relative in CANVAS_APP_RELATIVE_PATHS)


def read_canvas_app_source(root: Path) -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in canvas_app_paths(root))


def canvas_app_entry_href() -> str:
    return canvas_app_bootstrap_href()


def canvas_app_bootstrap_href() -> str:
    return "workbench/canvas/canvas-app-bootstrap.js"
